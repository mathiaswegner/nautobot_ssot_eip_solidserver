#!groovy
@Library('defaultlibrary')_

pipeline {
    agent none
    stages {
        stage('build the image') {
            agent {
                label 'python311'
            }
            stages {
                stage ('clean up workspace') {
                    steps {
                        sh '''
                        ls -la
                        rm -f ./*.tar.gz
                        rm -f ./*.whl
                        rm -f ./dist/*
                        rm -rf ~/.aws/credentials
                        '''
                    }
                }
                stage ('build dev') {
                    when {
                        branch 'develop'
                    }
                    steps {
                        withCredentials([usernamePassword(credentialsId:'isc-penn-tse-services-deploy-key', passwordVariable: 'GITLAB_KEY', usernameVariable: 'GITLAB_USER')]){
                            sh '''
                            git pull --tags https://${GITLAB_USER}:${GITLAB_KEY}@gitlab.com/isc-penn/tse/services/sourceoftruth/nautobot_ssot_eip_solidserver.git
                            '''
                        }
                        sh '''
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
                        withCredentials([usernamePassword(credentialsId:'isc-penn-tse-services-deploy-key', passwordVariable: 'GITLAB_KEY', usernameVariable: 'GITLAB_USER')]){
                            sh '''
                            git fetch --tags https://${GITLAB_USER}:${GITLAB_KEY}@gitlab.com/isc-penn/tse/services/sourceoftruth/nautobot_ssot_eip_solidserver.git
                            '''
                        }
                        sh '''
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
