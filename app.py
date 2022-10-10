import streamlit as st
import pandas as pd
import numpy as np
import streamlit.components.v1 as components
from clip_client import Client
import os
import numpy as np
import logging
import faiss
import pickle
import sys
from PIL import Image
from pathlib import Path

st.set_page_config(page_title = "QazPatent",layout = 'wide')


def delete_files_dir(dir):
    st.session_state['search'] = False
    for f in Path(dir).glob("*"):
        if f.is_file():
            f.unlink()

# @st.cache(allow_output_mutation=True)
def get_all_files(dir, carousel):
    listOfFiles = []
    for (dirpath, dirnames, filenames) in os.walk(dir):
        if carousel:
            listOfFiles += [os.path.join(dirpath.replace('frontend/public/', ''), file)
                            for file in filenames]
        else:
            listOfFiles += [os.path.join(dirpath, file)
                            for file in filenames]
    return listOfFiles


@st.cache(allow_output_mutation=True)
def get_config():
    index = faiss.read_index("index/test2.index")
    res = faiss.StandardGpuResources()
    index = faiss.index_cpu_to_gpu(res, 0, index)
    client = Client('grpc://0.0.0.0:51000')
    listOfFiles = get_all_files('frontend/public/dataset/Logos', False)
    return index, client, listOfFiles


# @st.cache(allow_output_mutation=True)
def find_similar_imgs(c, index, img_paths, listOfFiles1):
    encoding = c.encode(img_paths)
    similar_vecs = index.search(encoding, 10)
    similar_ids = similar_vecs[1][0]
    similar_img_paths = []
    for i in similar_ids:
        similar_img_paths.append(listOfFiles1[i])
    return similar_img_paths


c3, c1, c2 = st.columns((20,1,20))
# img_logo = Image.open('logo.png')
with c1:
    st.image('public/logo.png', width = 100)
    # st.write('tets')
# with c2:
#     st.markdown('<h1 style ="font-family:Geneva, sans-serif; margin-left: 3.5rem; margin-top: 0.1rem">QazPatent Demo<a style="color:darkred"></a></h1>', unsafe_allow_html=True)
r3, r1, r2 = st.columns((20,15,20))
# img_logo = Image.open('logo.png')
with r1:
    st.markdown('<h1 style ="font-family:Geneva, sans-serif; margin-left: 3.5rem;">Qaz<a style="color:darkred">Patent</a> Demo</h1>', unsafe_allow_html=True)
st.header('Поиск похожих логотипов')
search_btn = False

if 'search' not in st.session_state:
    st.session_state['search'] = False

index, client, listOfFiles = get_config()
index_options = [
    'index1'
]
model_options = [
    'CLIP (ViT-32)',
    'RESNET101',
    'efficientnetv2_rw_t'
]

col1, col2 = st.columns([1,1])

with col1:

    uploaded_files = st.file_uploader(
        "Загрузить картинку", type=['png', 'jpg', 'jpeg'], accept_multiple_files=False, help="Hello", on_change=delete_files_dir("frontend/public/uploaded"))
    chosed_index = st.selectbox(
     'Выбрать датаесет',
     index_options)
    chosed_model = st.selectbox(
     'Выбрать модель векторизации картинки',
     model_options)
    
    if uploaded_files:
        search_btn = st.button('Поиск')
with col2:
    
    if uploaded_files:
        uploaded_file = uploaded_files
        # for uploaded_file in uploaded_files:
        im = Image.open(uploaded_file)
        # If is png image
        # with open(os.path.join("frontend/public/uploaded", uploaded_file.name), "wb") as f:
        #         f.write(uploaded_file.getbuffer())
        if im.format == 'PNG':
            # and is not RGBA
            
            if im.mode != 'RGBA':
                im.convert("RGBA").save(f"frontend/public/uploaded/{uploaded_file.name}")
            else:
                with open(os.path.join("frontend/public/uploaded", uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
        else:
            with open(os.path.join("frontend/public/uploaded", uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        imageUrls = get_all_files('frontend/public/uploaded', True)
        imageUrls_for_model = get_all_files('frontend/public/uploaded', False)
        # if len(uploaded_files) == 1:
        #     st.markdown('<p style ="margin-bottom:33px; matgin-top:10px"> </p>', unsafe_allow_html=True)
        #     st.image(im, width=400)
        # else:
        imageCarouselComponent = components.declare_component(
            "image-carousel-component", path="frontend/public")
        
        selectedImageUrl = imageCarouselComponent(imageUrls=imageUrls, height=400)
        if selectedImageUrl is not None:
            st.image(selectedImageUrl)



if search_btn:
    st.session_state['search'] = True
    similar_img_paths = find_similar_imgs(
        client, index, imageUrls_for_model, listOfFiles)
    st.subheader('Похожие лого')
    imageCarouselComponent = components.declare_component(
        "image-carousel-component", path="frontend/public")
    imageUrls2 = [item.replace('frontend/public/', '')
                  for item in similar_img_paths]
    selectedImageUrl2 = imageCarouselComponent(
        imageUrls=imageUrls2, height=500)
    if selectedImageUrl2 is not None:
        st.image(selectedImageUrl2)

if uploaded_files and st.session_state['search']:
    if st.button('Сбросить'):
        uploaded_files = []
        st.session_state['search'] = False
        delete_files_dir("frontend/public/uploaded")
        st.experimental_rerun()
    
