FROM python:3.12-slim

WORKDIR /app

COPY streamlit_app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY streamlit_app/ streamlit_app/

EXPOSE 8501

ENV BACKEND_URL="http://localhost:8000/api/v1"
ENV STREAMLIT_API_TOKEN="dev-token"

CMD ["sh", "-c", "streamlit run streamlit_app/app.py --server.port ${PORT:-8501} --server.address 0.0.0.0"]
