FROM docker.io/nextstrain/base:latest

ARG MAPBOX_ACCESS_TOKEN
ARG MAPBOX_STYLE_OWNER=mapbox
ARG MAPBOX_STYLE_ID=light-v11

WORKDIR /opt/auspice-custom

COPY auspice-config.json .

RUN test -n "${MAPBOX_ACCESS_TOKEN}" \
    && sed -i \
        -e "s|__MAPBOX_ACCESS_TOKEN__|${MAPBOX_ACCESS_TOKEN}|g" \
        -e "s|__MAPBOX_STYLE_OWNER__|${MAPBOX_STYLE_OWNER}|g" \
        -e "s|__MAPBOX_STYLE_ID__|${MAPBOX_STYLE_ID}|g" \
        auspice-config.json \
    && auspice build --verbose --extend auspice-config.json

ENV HOST=0.0.0.0
ENV PORT=8100

CMD ["auspice", "view", "--verbose", "--customBuildOnly", "--datasetDir=/data", "--narrativeDir=/data"]
