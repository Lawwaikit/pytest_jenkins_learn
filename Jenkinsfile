
pipeline {
    agent any
    environment {
        PROJECT_NAME = 'pytest_jenkins_learn'
        PYTHONUNBUFFERED = '1'
        PATH = "${WORKSPACE}/venv/bin:${env.PATH}"
        GIT_URL = 'https://github.com/Lawwaikit/pytest_jenkins_learn.git'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }    
    
    parameters {
        choice(
            name: 'TEST_ENV',
            choices: ['test', 'staging'],
            description: '选择测试环境'
        )
        choice(
            name: 'TEST_SCOPE',
            choices: ['all', 'smoke'],
            description: '选择测试范围'
        )
    }

    stages {
        stage('Clean') {
            steps {
                echo '清理旧工作空间'
                deleteDir()
                sh '''
                    rm -rf allure-results/* reports/*
                '''
                
            }
        }
        stage('查看构建信息'){
            steps{  
                echo "项目名称：${env.PROJECT_NAME}"
                echo "Job 名称: ${env.JOB_NAME}"
                echo "构建 ID: ${env.BUILD_ID}"
                echo "构建编号：${env.BUILD_NUMBER}"
                echo "工作目录：${env.WORKSPACE}"
                echo "Jenkins 服务地址：${env.JENKINS_URL}"
                echo "测试环境：${params.TEST_ENV}"
                echo "构建编号：${currentBuild.number}"
                echo "构建结果：${currentBuild.currentResult}"
                echo "构建持续时间：${currentBuild.duration} ms"
                echo "构建完整显示名称：${currentBuild.fullDisplayName}"

                script {
                    def testConfig = [
                        test: 'http://test.example.com',
                        staging: 'http://staging.example.com'
                    ]
                    def targetUrl = testConfig[params.TEST_ENV]
                    echo "测试地址：${targetUrl}"
                }
            }  
        }
        stage('Checkout') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: 'main']], // 也可以是具体的 tag 或 SHA
                    userRemoteConfigs: [[
                        url: env.GIT_URL,
                    ]]
                ])
                script{
                    echo env.GIT_BRANCH
                }
            }
        }
        stage('Install安装依赖') {
            steps {
                sh '''
                python -m venv venv/
                chmod +x venv/bin/activate
                . venv/bin/activate
                python -m pip install -r requirements.txt
                '''
            }
        }
        stage('Prepare Allure History') {
            steps {
                script {
                    if (fileExists('allure-report/history')) {
                        sh '''
                            mkdir -p allure-results/history

                            cp -r allure-report/history/* \
                                allure-results/history/
                        '''
                    }
                }
            }
        }
        stage('执行pytest测试') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        def testCommand = 'pytest -v '
                        if (params.TEST_SCOPE == 'smoke') {
                            testCommand += ' -m smoke'
                        }
                        testCommand += ' --junitxml=reports/junit.xml'
                        testCommand += ' --alluredir=allure-results'
                        sh testCommand
                    }
                }
            }
        }
    }
    post {
        success {
            echo 'Build completed successfully.'
        }
        failure {
            echo 'Build failed. Check the stage logs.'
        }
        always {
            script {
                echo 'Pipeline execuate finished.'
                echo "最终构建状态：${currentBuild.currentResult}"
                echo "构建耗时：${currentBuild.duration} ms"

                junit 'reports/junit.xml'
                archiveArtifacts artifacts: 'allure-results/**,reports/**',
                    allowEmptyArchive: true
            }
            allure(
                results: [[path: 'allure-results']]
            )
        }
    }
}
