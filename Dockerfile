#FROM python:3.9-slim-buster
FROM docker-proxy.devops.projectronin.io/ronin/base/python-builder:1.0.0 as builder

# we need the version of python to be correct (python 10.9)
# we need everything in the Pipfile to create the environment

COPY --chown=ronin:ronin requirements.txt .
#COPY requirements.txt .

RUN pip install --user -r requirements.txt

#FROM docker-proxy.devops.projectronin.io/ronin/base/python-base:1.0.0 as runtime
#COPY --from=builder --chown=ronin:ronin /app/.local/ /app/.local
#COPY --chown=ronin:ronin src ./src

EXPOSE 8000
USER ronin
ENTRYPOINT [ "./entrypoint.sh" ]
CMD [ "python", "-m", "src.ronin_ctl", "serve", "--port", "8000" ]