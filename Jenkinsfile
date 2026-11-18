
pipeline {
    agent any

    environment {
        PROJECT_NAME = 'pytest_jenkins_learn'
        PYTHONUNBUFFERED = '1'
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
                        url: 'https://github.com/Lawwaikit/pytest_jenkins_learn.git',
                    ]]
                ])
                script{
                    echo env.GIT_BRANCH
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
            echo 'Pipeline execuate finished.'
        }
    }
}
