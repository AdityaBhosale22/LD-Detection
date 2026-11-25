// CD pipeline: test -> build Docker image -> push to AWS ECR -> deploy to EC2.
//
// Jenkins setup (one time):
//   - Plugins: Pipeline, Docker Pipeline, SSH Agent, Credentials Binding
//   - Agent needs: docker, aws CLI v2
//   - Credentials:
//       aws-ecr-push : "Username with password" = AWS access key id / secret key
//                      (IAM user with ECR push permissions)
//       ec2-ssh-key  : "SSH Username with private key" for the EC2 instance
//   - Set AWS_ACCOUNT_ID and EC2_HOST below (or as job parameters).

pipeline {
    agent any

    environment {
        AWS_REGION     = 'ap-south-1'
        AWS_ACCOUNT_ID = '123456789012'          // change me
        ECR_REPO       = 'ld-detection'
        EC2_HOST       = 'ec2-user@your-ec2-ip'  // change me
        REGISTRY       = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        IMAGE          = "${REGISTRY}/${ECR_REPO}"
        TAG            = "${env.BUILD_NUMBER}"
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Build image') {
            steps {
                sh 'docker build -t $IMAGE:$TAG -t $IMAGE:latest .'
            }
        }

        stage('Test') {
            steps {
                // Run the Django test suite inside the image we just built
                sh 'docker run --rm --entrypoint "" $IMAGE:$TAG python manage.py test tests'
            }
        }

        stage('Push to ECR') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(credentialsId: 'aws-ecr-push',
                                                  usernameVariable: 'AWS_ACCESS_KEY_ID',
                                                  passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
                    sh '''
                        aws ecr get-login-password --region $AWS_REGION \
                          | docker login --username AWS --password-stdin $REGISTRY
                        docker push $IMAGE:$TAG
                        docker push $IMAGE:latest
                    '''
                }
            }
        }

        stage('Deploy to EC2') {
            when { branch 'main' }
            steps {
                sshagent(credentials: ['ec2-ssh-key']) {
                    // Copy the compose file, then pull the new image and restart.
                    // The EC2 instance role grants ECR read + S3 write, so no keys live on the server.
                    sh '''
                        scp -o StrictHostKeyChecking=no docker-compose.yml $EC2_HOST:~/app/docker-compose.yml
                        ssh -o StrictHostKeyChecking=no $EC2_HOST "
                          cd ~/app &&
                          aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $REGISTRY &&
                          IMAGE=$IMAGE:$TAG docker compose pull web &&
                          IMAGE=$IMAGE:$TAG docker compose up -d --no-build &&
                          docker image prune -f
                        "
                    '''
                }
            }
        }

        stage('Smoke test') {
            when { branch 'main' }
            steps {
                sshagent(credentials: ['ec2-ssh-key']) {
                    sh '''
                        ssh -o StrictHostKeyChecking=no $EC2_HOST "
                          for i in 1 2 3 4 5 6 7 8 9 10; do
                            curl -fsS http://localhost/healthz/ && exit 0; sleep 3;
                          done; exit 1
                        "
                    '''
                }
            }
        }
    }

    post {
        always {
            sh 'docker image rm $IMAGE:$TAG $IMAGE:latest || true'
        }
    }
}
