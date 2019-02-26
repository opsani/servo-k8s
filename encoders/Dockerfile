FROM openjdk:8-jre-alpine

ADD encoder.sh /

RUN chmod a+x /encoder.sh

WORKDIR /

ENTRYPOINT [ "/encoder.sh" ]
