FROM apache/airflow:2.10.5-python3.10

USER root
COPY . /opt/project
RUN chown -R airflow:0 /opt/project

USER airflow
RUN pip install --no-cache-dir -r /opt/project/airflow/requirements.txt

WORKDIR /opt/project
ENV PYTHONPATH=/opt/project
ENV DBT_PROFILES_DIR=/opt/project/dbt
