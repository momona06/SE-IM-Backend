FROM python:3.10
# FROM python:3.9

ENV DEPLOY=1

ENV HOME=/opt/tmp

WORKDIR $HOME

COPY requirements.txt .

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

COPY . .

EXPOSE 80

CMD ["sh", "start.sh"]