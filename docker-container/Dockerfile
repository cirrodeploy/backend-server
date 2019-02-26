FROM amazonlinux:latest

WORKDIR /usr/local/service

RUN yum update -y && \
    yum install -y ca-certificates unzip

# Download Terraform
COPY ./TERRAFORM_URL.txt /usr/local/service/TERRAFORM_URL.txt
RUN curl -L --silent $(cat /usr/local/service/TERRAFORM_URL.txt) > /terraform.zip && \
    unzip /terraform.zip -d /bin/ && \
    rm /terraform.zip
