#!groovy
@Library('defaultlibrary')_

pipeline {
    agent none
    stages {
        stage('build the image') {
            agent {
                label 'dockerbuilder-py39'
            }
            stages {
                stage ('clean up workspace') {
                    steps {
                        sh '''
                        ls -la
                        rm -f ./*.tar.gz
                        rm -f ./*.whl
                        rm -rf ~/.aws/credentials
                        '''
                    }
                }
                stage ('build dev') {
                    when {
                        branch 'develop'
                    }
                    steps {
                        sh '''
                        pip3 install build twine
                        python3 -m build
                        mv pypirc.txt ~/.pypirc
                        '''
                        withCredentials([usernamePassword(credentialsId:'nautobot-plugins-write', passwordVariable: 'GITLAB_KEY', usernameVariable: 'GITLAB_USER')]){
                            sh '''
                            echo "username = ${GITLAB_USER}" >> ~/.pypirc
                            echo "password = ${GITLAB_KEY}" >> ~/.pypirc
                            python3 -m twine upload --repository gitlab-nautobot-plugins dist/*
                            rm ~/.pypirc
                            '''
                        }
                    }
                }
                stage ('build prod') {
                    when {
                        branch 'production'
                    }
                    steps {
                        sh '''
                        pip3 install build twine
                        python3 -m build
                        mv pypirc.txt ~/.pypirc
                        '''
                        withCredentials([usernamePassword(credentialsId:'nautobot-plugins-write', passwordVariable: 'GITLAB_KEY', usernameVariable: 'GITLAB_USER')]){
                            sh '''
                            echo "username = ${GITLAB_USER}" >> ~/.pypirc
                            echo "password = ${GITLAB_KEY}" >> ~/.pypirc
                            python3 -m twine upload --repository gitlab-nautobot-plugins dist/*
                            rm ~/.pypirc
                            '''
                        }
                    }
                }
            }
        }
    }
}
