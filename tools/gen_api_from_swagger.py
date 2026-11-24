#!/usr/bin/env python3
"""把 Swagger / OpenAPI 文档转换成 pytest 可直接调用的 Python API 类。

设计目标：业务接口变化时，只重新运行本脚本，关键字层的调用代码尽量不动。
  - 一个 tag 生成一个类（类名可通过 --class-map 固定）；
  - 一个接口生成一个方法（方法名可通过 --method-map 固定）；
  - 方法签名固定为 path_params/query/body/headers，由关键字层组装，接口字段变化不改签名；
  - 方法 docstring 带 summary、description、HTTP 方法/路径与接口参数说明（不逐条解释响应码）；
  - --check 模式可放进 CI：文档与代码不一致时退出码为 1。

用法：
  # 1) 从运行中的服务读取 /openapi.json（推荐，最真实）
  python tools/gen_api_from_swagger.py --url http://localhost:30080/openapi.json --out api/generated

  # 2) 从本地规范文件读取（JSON；装了 PyYAML 也支持 YAML）
  python tools/gen_api_from_swagger.py --spec openapi.json --out api/generated

  # 3) 直接从 FastAPI 源码导入 app 并调用 app.openapi()（无需启动服务）
  python tools/gen_api_from_swagger.py \
      --app main:app \
      --app-path ../docker_learn/fastapi/app \
      --out api/generated

  # 4) CI 漂移检查（不写文件，发现差异退出 1）
  python tools/gen_api_from_swagger.py --spec openapi.json --check
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import keyword
import os
import re
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}

KNOWN_TAG_CLASSES = {
    "认证": "AuthAPI",
    "用户管理": "UserAPI",
    "钱包管理": "WalletAPI",
    "交易": "TradeAPI",
    "运维探针": "OpsAPI",
    "连通性探测": "ProbeAPI",
}

RESERVED_ARGS = {"self", "headers", "extra", "body", "query",
                 "path_params", "name", "kwargs"}

UNSET = object()


@dataclass
class Param:
    name: str                 # 原始参数名（HTTP 上的名字）
    arg_name: str             # Python 方法签名里的名字
    location: str             # path / query / body
    hint: str                 # 类型注解
    required: bool
    has_default: bool
    default: Any
    description: str = ""


def to_snake(value: str) -> str:
    text = re.sub(r"[^0-9A-Za-z]+", "_", str(value)).strip("_")
    text = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", text)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    return re.sub(r"_+", "_", text).lower()


def safe_arg_name(name: str) -> str:
    arg = to_snake(name)
    if not arg or keyword.iskeyword(arg) or arg in RESERVED_ARGS or arg[0].isdigit():
        arg = f"{arg or 'arg'}_"
    return arg


def class_name_for(tag: str, index: int, class_map: dict[str, str]) -> str:
    if tag in class_map:
        return class_map[tag]
    if tag in KNOWN_TAG_CLASSES:
        return KNOWN_TAG_CLASSES[tag]
    words = re.sub(r"[^0-9A-Za-z]+", " ", tag).split()
    name = "".join(w[:1].upper() + w[1:] for w in words)
    if not name or not name[0].isalpha():
        name = f"Tag{index}"
    return name


def method_name_for(operation: dict, path: str, http_method: str, used: set[str],
                    method_map: dict[str, str]) -> str:
    operation_id = operation.get("operationId", "")
    if operation_id in method_map:
        name = method_map[operation_id]
    else:
        name = to_snake(operation_id)
        suffix = f"_{http_method}"
        if name.endswith(suffix):
            name = name[: -len(suffix)]
        tokens = [to_snake(part) for part in path.split("/")
                  if part and not part.startswith("{")]
        for start in range(len(tokens)):
            path_suffix = "_".join(tokens[start:])
            if path_suffix and name.endswith("_" + path_suffix):
                name = name[: -len(path_suffix) - 1]
                break
        if not name or keyword.iskeyword(name):
            name = to_snake(http_method) + "_" + "_".join(
                to_snake(p.replace("{", "by_").replace("}", "")) for p in path.split("/") if p
            )
    name = safe_arg_name(name).rstrip("_") or f"operation_{len(used) + 1}"
    base, number = name, 2
    while name in used:
        name = f"{base}_{number}"
        number += 1
    used.add(name)
    return name


def json_pointer(spec: dict, ref: str) -> dict:
    node: Any = spec
    for part in ref.lstrip("#/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        node = node.get(part, {}) if isinstance(node, dict) else {}
    return node if isinstance(node, dict) else {}


def resolve_ref(spec: dict, node: Any) -> dict:
    seen: set[str] = set()
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if ref in seen:
            return {}
        seen.add(ref)
        node = json_pointer(spec, ref)
    return node if isinstance(node, dict) else {}


def merged_schema(spec: dict, schema: dict) -> dict:
    node = resolve_ref(spec, schema)
    if "allOf" in node:
        properties: dict[str, Any] = {}
        required: list[str] = []
        for part in node["allOf"]:
            child = merged_schema(spec, part)
            properties.update(child.get("properties", {}))
            required.extend(child.get("required", []))
        properties.update(node.get("properties", {}))
        required.extend(node.get("required", []))
        return {"type": "object", "properties": properties,
                "required": list(dict.fromkeys(required))}
    return node


def type_hint(spec: dict, schema: dict) -> str:
    node = resolve_ref(spec, schema)
    kind = node.get("type")
    if isinstance(kind, list):
        kind = next((item for item in kind if item != "null"), "object")
    return {
        "integer": "int", "number": "float", "boolean": "bool", "string": "str",
        "array": "list", "object": "dict", "file": "bytes", "null": "None",
    }.get(kind, "Any")


def normalize_spec(spec: dict) -> dict:
    """兼容 Swagger 2.0，并合并 path 级公共参数。"""
    if "openapi" not in spec and "swagger" not in spec:
        raise ValueError("输入文件既没有 openapi 字段也没有 swagger 字段，不是有效的 API 规范")
    result = json.loads(json.dumps(spec))  # 深拷贝，避免改动调用方数据
    if "openapi" not in result:
        host = result.get("host")
        base_path = result.get("basePath", "")
        scheme = (result.get("schemes") or ["https"])[0]
        result["openapi"] = "3.0.0"
        result["servers"] = [{"url": f"{scheme}://{host}{base_path}"}] if host else []
        result["components"] = {
            "schemas": result.get("definitions", {}),
            "securitySchemes": result.get("securityDefinitions", {}),
        }
        for path_item in result.get("paths", {}).values():
            if not isinstance(path_item, dict):
                continue
            for method, operation in path_item.items():
                if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                    continue
                parameters = operation.get("parameters", [])
                for parameter in parameters:
                    if parameter.get("in") == "body":
                        operation["requestBody"] = {
                            "required": parameter.get("required", False),
                            "content": {"application/json": {"schema": parameter.get("schema", {})}},
                        }
                        break
                operation["parameters"] = [p for p in parameters if p.get("in") != "body"]

    for path_item in result.get("paths", {}).values():
        if not isinstance(path_item, dict):
            continue
        common = path_item.get("parameters", [])
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            operation["parameters"] = list(common) + list(operation.get("parameters", []))
    return result


def load_spec(args: argparse.Namespace) -> dict:
    if args.url:
        with urllib.request.urlopen(args.url, timeout=args.timeout) as response:
            raw = response.read()
        return json.loads(raw)
    if args.spec:
        path = Path(args.spec)
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml
            except ImportError as exc:
                raise SystemExit("读取 YAML 规范需要 PyYAML：pip install PyYAML") from exc
            return yaml.safe_load(text)
        return json.loads(text)
    if args.app:
        return load_from_app(args.app, args.app_path)
    raise SystemExit("请指定 --url、--spec 或 --app 中的一个 API 文档来源")


def load_from_app(app_spec: str, app_path: str | None) -> dict:
    """导入 FastAPI 应用对象并导出 app.openapi()。

    FinTrade 的 main.py 在导入时会读取 secret 文件，这里准备临时占位文件，
    只用于生成规范，不连接 MySQL/Redis。
    """
    module_name, _, attribute = app_spec.partition(":")
    attribute = attribute or "app"
    if app_path:
        sys.path.insert(0, str(Path(app_path).resolve()))

    temp_path: str | None = None
    if not os.environ.get("MYSQL_PASSWORD"):
        os.environ["MYSQL_PASSWORD"] = "dev-only-for-openapi"
    if not os.environ.get("JWT_SECRET"):
        os.environ["JWT_SECRET"] = "dev-only-for-openapi"
    password_file = os.environ.get("MYSQL_PASSWORD_FILE")
    if not password_file or not Path(password_file).is_file():
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
        handle.write("dev-only-for-openapi\n")
        handle.close()
        temp_path = handle.name
        os.environ["MYSQL_PASSWORD_FILE"] = temp_path
    try:
        module = importlib.import_module(module_name)
        app = getattr(module, attribute)
        return app.openapi()
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


def body_parameters(spec: dict, operation: dict) -> tuple[list[Param], bool]:
    schema: dict = {}
    required = False
    request_body = resolve_ref(spec, operation.get("requestBody", {}))
    if request_body:
        required = bool(request_body.get("required", False))
        content = request_body.get("content", {})
        media = content.get("application/json") or next(iter(content.values()), {})
        schema = media.get("schema", {})
    if not schema:
        for parameter in operation.get("parameters", []):
            if parameter.get("in") == "body":
                schema = parameter.get("schema", {})
                required = bool(parameter.get("required", False))
                break
    merged = merged_schema(spec, schema)
    required_names = set(merged.get("required", []))
    params: list[Param] = []
    for name, field_schema in merged.get("properties", {}).items():
        field = resolve_ref(spec, field_schema)
        is_required = name in required_names
        params.append(Param(
            name=name,
            arg_name=safe_arg_name(name),
            location="body",
            hint=type_hint(spec, field),
            required=is_required,
            has_default=not is_required,
            default=None if is_required else (
                field["default"] if "default" in field else UNSET
            ),
            description=field.get("description", ""),
        ))
    return params, required


def other_parameters(spec: dict, operation: dict) -> list[Param]:
    params: list[Param] = []
    seen: set[tuple[str, str]] = set()
    for raw in operation.get("parameters", []):
        parameter = resolve_ref(spec, raw)
        location = parameter.get("in")
        if location not in {"path", "query", "header", "cookie"}:
            continue
        name = parameter.get("name", "")
        if not name or (location, name) in seen:
            continue
        seen.add((location, name))
        is_required = location == "path" or bool(parameter.get("required", False))
        schema = parameter.get("schema", parameter)
        params.append(Param(
            name=name,
            arg_name=safe_arg_name(name),
            location=location,
            hint=type_hint(spec, schema),
            required=is_required,
            has_default=not is_required,
            default=None if is_required else (
                schema["default"] if "default" in schema else UNSET
            ),
            description=parameter.get("description", ""),
        ))
    return params


COMMON_SIGNATURE = (
    "self, *, path_params: dict | None = None, query: dict | None = None, "
    "body: dict | None = None, headers: dict | None = None"
)


def render_docstring(spec: dict, operation: dict, tag: str, path: str, http_method: str,
                     params: list[Param]) -> str:
    def clean(value: Any) -> str:
        return str(value or "").replace('"""', "'''").replace("\r", "").strip()

    summary = clean(operation.get("summary")) or f"{http_method.upper()} {path}"
    description = clean(operation.get("description"))
    lines = [summary+" "+f"{http_method.upper()} {path}"]
    if description:
        lines.extend(["", description])
    if params:
        lines.extend(["", "参数:"])
        for param in params:
            flag = "必填" if param.required else "可选"
            detail = f"    {param.name} ({param.hint}, {flag}, {param.location})"
            if param.description:
                detail += f": {clean(param.description)}"
            lines.append(detail)
    return '        """' + "\n        ".join(lines) + '\n        """'


def render_method(spec: dict, operation: dict, tag: str, path: str, http_method: str,
                  name: str, params: list[Param], tag_metadata: list | None = None) -> list[str]:
    """生成通用签名的方法：参数由关键字层组装，接口字段变化不影响方法签名。"""
    step_name = operation.get("summary") or f"{http_method.upper()} {path}"
    lines = [f"    def {name}({COMMON_SIGNATURE}) -> ApiResponse:"]
    lines.append(render_docstring(spec, operation, tag, path, http_method, params))
    lines.extend([
        "        return self._request(",
        f"            {http_method.upper()!r}, {path!r},",
        "            path_params=path_params,",
        "            query=query,",
        "            body=body,",
        "            headers=headers,",
        f"            name={step_name!r},",
        "        )",
        "",
    ])
    return lines


def render_class(spec: dict, tag: str, class_name: str, operations: list[dict]) -> str:
    tag_description = ""
    for entry in operations[0]["tag_metadata"]:
        if entry.get("name") == tag:
            tag_description = str(entry.get("description", "")).replace('"""', "'''")
            break
    lines = [
        f'class {class_name}(BaseAPI):',
        f'    """{tag} 相关接口。',
    ]
    if tag_description:
        lines.append("")
        for line in tag_description.replace("\r", "").strip().splitlines():
            lines.append(f"    {line}" if line.strip() else "")
    lines.extend([
        "",
        "    接口由 OpenAPI 规范自动生成，方法签名固定；参数由关键字层组装。",
        "    未显式传 client 时自动使用 SessionManager 的当前登录会话。",
        "    由 tools/gen_api_from_swagger.py 自动生成，请勿手动修改；",
        "    接口变更后重新运行生成脚本，不要直接编辑本文件。",
        "",
        "    调用方式:",
        f"        api = {class_name}()",
        "        response = api.<method>(path_params=..., query=..., body=..., headers=...)",
        '    """',
        "",
    ])
    for operation in operations:
        lines.extend(render_method(spec=spec, **operation))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_module(class_name: str, tag: str, spec: dict, operations: list[dict]) -> str:
    info = spec.get("info", {})
    lines = [
        "# -*- coding: utf-8 -*-",
        '"""由 tools/gen_api_from_swagger.py 自动生成，请勿手动修改。',
        "",
        f"API: {info.get('title', 'Unknown')} {info.get('version', '')}",
        f"标签: {tag}",
        "重新生成: python tools/gen_api_from_swagger.py --url <服务地址>/openapi.json --out api/generated",
        '"""',
        "from __future__ import annotations",
        "",
        "from api.base import ApiResponse, BaseAPI",
        "",
        "",
    ]
    lines.append(render_class(spec, tag, class_name, operations))
    return "\n".join(lines)


def build_files(spec: dict, class_map: dict[str, str], method_map: dict[str, str]) -> dict[str, str]:
    normalized = normalize_spec(spec)
    grouped: dict[str, list[tuple[str, str, dict]]] = {}
    for path, item in normalized.get("paths", {}).items():
        if not isinstance(item, dict):
            continue
        for http_method, operation in item.items():
            if http_method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            tags = operation.get("tags") or ["默认"]
            tag = tags[0]
            grouped.setdefault(tag, []).append((path, http_method.lower(), operation))

    files: dict[str, str] = {}
    exports: list[str] = []
    class_names: dict[str, str] = {}
    for index, (tag, operations) in enumerate(grouped.items(), start=1):
        class_name = class_name_for(tag, index, class_map)
        class_names[tag] = class_name
        used_methods: set[str] = set()
        rendered = []
        for path, http_method, operation in operations:
            params = other_parameters(normalized, operation)
            body, _ = body_parameters(normalized, operation)
            params.extend(body)
            name = method_name_for(operation, path, http_method, used_methods, method_map)
            rendered.append({
                "operation": operation,
                "tag": tag,
                "path": path,
                "http_method": http_method,
                "name": name,
                "params": params,
                "tag_metadata": normalized.get("tags", []),
            })
        filename = f"{to_snake(class_name)}.py"
        files[filename] = render_module(class_name, tag, normalized, rendered)
        exports.append(class_name)

    init_lines = ['"""OpenAPI 自动生成的 API 类集合，请勿手动修改。"""', ""]
    init_lines.extend(f"from .{to_snake(name)} import {name}" for name in exports)
    init_lines.extend(["", f"__all__ = {json.dumps(exports, ensure_ascii=False)}", ""])
    files["__init__.py"] = "\n".join(init_lines)

    canonical = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
    manifest = {
        "generated_by": "tools/gen_api_from_swagger.py",
        "api_title": normalized.get("info", {}).get("title", ""),
        "api_version": normalized.get("info", {}).get("version", ""),
        "openapi_version": normalized.get("openapi", ""),
        "spec_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "tag_classes": class_names,
        "operation_count": sum(len(items) for items in grouped.values()),
    }
    files["_manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    return files


def load_json_mapping(path: str | None, description: str) -> dict[str, str]:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{description} 必须是 JSON 对象")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Swagger/OpenAPI -> Python API 类生成器")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="运行服务的 openapi.json 地址")
    source.add_argument("--spec", help="本地 openapi.json / openapi.yaml 路径")
    source.add_argument("--app", help="FastAPI 应用对象，如 main:app（无需启动服务）")
    parser.add_argument("--app-path", help="--app 模式下要加入 sys.path 的目录")
    parser.add_argument("--timeout", type=int, default=10, help="--url 读取超时秒数")
    parser.add_argument("--out", default="api/generated", help="输出目录")
    parser.add_argument("--class-map", help="JSON 文件：tag -> 类名，固定类名不随文档变化")
    parser.add_argument("--method-map", help="JSON 文件：operationId -> 方法名，固定方法名")
    parser.add_argument("--check", action="store_true", help="只检查生成结果是否落后于文档")
    args = parser.parse_args()

    try:
        spec = load_spec(args)
        files = build_files(
            spec,
            load_json_mapping(args.class_map, "--class-map"),
            load_json_mapping(args.method_map, "--method-map"),
        )
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(f"生成 API 代码失败：{type(exc).__name__}: {exc}") from exc

    out_dir = Path(args.out)
    if args.check:
        stale = []
        for name, content in files.items():
            target = out_dir / name
            if not target.is_file() or target.read_text(encoding="utf-8") != content:
                stale.append(name)
        if stale:
            print("API 文档已变化，请重新生成：" + ", ".join(sorted(stale)))
            raise SystemExit(1)
        print(f"API 代码与文档一致（{len(files)} 个文件）")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (out_dir / name).write_text(content, encoding="utf-8")
    print(f"已生成 {len(files)} 个文件到 {out_dir}：{', '.join(sorted(files))}")


if __name__ == "__main__":
    main()
