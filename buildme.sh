#!/bin/bash


rm -rf ._*
docker build -t streamlit-flac .
docker run -it --rm -p 8600:8501 streamlit-flac
