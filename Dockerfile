FROM node:22.23.4-bookworm-slim@sha256:aaa4b5baf1ecff3b283486bb1f90405cdda225a3e6f79660d2c559fa510a7292 AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/protocol
COPY protocol/package.json protocol/package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund
COPY protocol/packages ./packages
COPY protocol/scripts ./scripts
COPY protocol/LICENSE protocol/NOTICE /usr/share/doc/pins/
COPY LICENSE NOTICE /usr/share/doc/pins-app/
COPY source-manifest.json /usr/share/doc/pins/source-manifest.json
COPY --chmod=0555 app /opt/index-app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOME=/tmp
RUN mkdir -p /data && chown 1000:1000 /data
USER 1000:1000
STOPSIGNAL SIGTERM
ENTRYPOINT ["python3", "/opt/index-app/indexapp.py"]
CMD ["--help"]

FROM runtime AS verified
COPY fixtures/ /opt/protocol/
RUN python3 -c "import glob,subprocess; subprocess.run(['node','--experimental-strip-types','--test',*sorted(glob.glob('packages/indexer/*.test.ts'))],check=True)" \
    && printf 'Read-only indexer fixture tests passed\n' > /tmp/pins-tests-passed

FROM runtime
COPY --from=verified /tmp/pins-tests-passed /usr/share/doc/pins/validation.txt
