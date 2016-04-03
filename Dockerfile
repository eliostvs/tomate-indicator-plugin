FROM eliostvs/tomate

ENV PROJECT /code/

COPY ./ $PROJECT

RUN apt-get clean && apt-get update -qq && apt-get install -y gir1.2-appindicator3-0.1
RUN easy_install pytest pytest-cov

WORKDIR $PROJECT

ENTRYPOINT ["make"]

CMD ["test"]