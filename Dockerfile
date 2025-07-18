FROM --platform=linux/amd64 python:3.8.6
RUN pip install --upgrade pip

WORKDIR /code

COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r  requirements.txt

COPY ./src ./src

EXPOSE 80

# CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80", "--reload"] # disabling relaod
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]

# docker build -t  ctocds/ctsapi2:0.1 .
# docker container run -p 7000:80 58f0b10b4183416545fb4d6c2b889e5eaad9795260f0f55a2e678a29329c8894
# docker exec -it <container_id> sh


# volumn docker run --name  cts-container -p 80:80 -d -v $(pwd):/code ctsapi2



#******** s3 deploy
#* VIEW Command here  https://us-west-1.console.aws.amazon.com/ecr/private-registry/repositories?region=us-west-1

# introduction on how to set up ALB and Targetgroup and policy http://cds-1502529271.us-west-1.elb.amazonaws.com/

#******** google cloud
# buid image    : docker build -t cdszone .
# name of image : us-west2-docker.pkg.dev/polling-apps/core/cdszone
# tag image     : docker tag cdszone us-west2-docker.pkg.dev/polling-apps/core/cdszone:lastest
# push image    : docker push us-west2-docker.pkg.dev/polling-apps/core/cdszone:lastest


