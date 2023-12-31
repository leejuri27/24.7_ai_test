import os
import sys
import streamlit as st
import cv2
import tempfile


BASE_DIR = os.path.abspath(os.path.join(__file__, '../../'))
sys.path.append(BASE_DIR)


from utils import get_mediapipe_pose
from process_frame_squat import ProcessFrame as ProcessFrameSquat
from process_frame_lunge import ProcessFrame as ProcessFrameLunge
from process_frame_pushup import ProcessFrame as ProcessFramePushup
from thresholds import thresholds_squat, thresholds_lunge, thresholds_pushup



# st.title('AI Fitness Trainer: Squats Analysis')

type = st.radio('Type of exercise', ['Squat', 'Lunge', 'Pushup'], horizontal=True)



thresholds = None 


# Initialize face mesh solution
pose = get_mediapipe_pose()


download = None

if 'download' not in st.session_state:
    st.session_state['download'] = False


output_video_file = f'output_recorded.mp4'

if os.path.exists(output_video_file):
    os.remove(output_video_file)


with st.form('Upload', clear_on_submit=True):
    up_file = st.file_uploader("Upload a Video", ['mp4','mov', 'avi'])
    uploaded = st.form_submit_button("Upload")

stframe = st.empty()

ip_vid_str = '<p style="font-family:Helvetica; font-weight: bold; font-size: 16px;">Input Video</p>'
warning_str = '<p style="font-family:Helvetica; font-weight: bold; color: Red; font-size: 17px;">Please Upload a Video first!!!</p>'

warn = st.empty()


download_button = st.empty()

if up_file and uploaded:
    
    download_button.empty()
    tfile = tempfile.NamedTemporaryFile(delete=False)

    try:
        warn.empty()
        tfile.write(up_file.read())

        vf = cv2.VideoCapture(tfile.name)

        # ---------------------  처리된 비디오 프레임을 작성합니다 --------------------
        fps = int(vf.get(cv2.CAP_PROP_FPS))
        width = int(vf.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(vf.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_size = (width, height)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_output = cv2.VideoWriter(output_video_file, fourcc, fps, frame_size)
        # -----------------------------------------------------------------------------

        if type == 'Squat':
            thresholds = thresholds_squat()
            upload_process_frame = ProcessFrameSquat(thresholds=thresholds, fps=fps, frame_size=frame_size)
        elif type == 'Lunge':
            thresholds = thresholds_lunge()
            upload_process_frame = ProcessFrameLunge(thresholds=thresholds,fps=fps, frame_size=frame_size)
        elif type == 'Pushup':
            thresholds = thresholds_pushup()
            upload_process_frame = ProcessFramePushup(thresholds=thresholds, fps=fps, frame_size=frame_size)
        
        txt = st.sidebar.markdown(ip_vid_str, unsafe_allow_html=True)   
        ip_video = st.sidebar.video(tfile.name) 

        while vf.isOpened():
            ret, frame = vf.read()
            if not ret:
                break

            # 처리하기 전에 프레임을 BGR에서 RGB로 변환합니다.
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            out_frame = upload_process_frame.process(frame, pose)
            stframe.image(out_frame)
            video_output.write(out_frame[...,::-1])

        
        vf.release()
        video_output.release()
        stframe.empty()
        ip_video.empty()
        txt.empty()
        tfile.close()
    
    except AttributeError:
        warn.markdown(warning_str, unsafe_allow_html=True)   



if os.path.exists(output_video_file):
    with open(output_video_file, 'rb') as op_vid:
        download = download_button.download_button('Download Video', data = op_vid, file_name='output_recorded.mp4')
    
    if download:
        st.session_state['download'] = True



if os.path.exists(output_video_file) and st.session_state['download']:
    os.remove(output_video_file)
    st.session_state['download'] = False
    download_button.empty()