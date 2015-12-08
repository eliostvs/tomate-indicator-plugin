FROM eliostvs/tomate-gtk

ENV PROJECT /code/

COPY ./ $PROJECT

RUN apt-get update -qq && apt-get install -y gir1.2-appindicator3-0.1

WORKDIR $PROJECT

ENTRYPOINT ["make"]

CMD ["test"]