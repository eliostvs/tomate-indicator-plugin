FROM eliostvs/tomate

RUN apt-get clean && apt-get update -qq && apt-get install -y gir1.2-appindicator3-0.1

WORKDIR /code/

ENTRYPOINT ["make"]

CMD ["test"]
