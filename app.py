from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

app = Flask(__name__)

def create_gantt_chart(data):
    fig, ax = plt.subplots(figsize=(12, 4))
    for index, row in data.iterrows():
        plt.barh(y=row['Job'], width=row['Pj'], left=row['Thời gian bắt đầu'])
    plt.title('Biểu đồ Gantt', fontsize=15, fontweight='bold')
    plt.xlabel("Thời gian (ngày)", fontweight='bold')
    plt.ylabel("Job", fontweight='bold')

    img_stream = io.BytesIO()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)

    img_data = base64.b64encode(img_stream.read()).decode('utf-8')
    result_df = data[['Job', 'Pj', 'Thời gian bắt đầu', 'Thời gian kết thúc']]
    return img_data, result_df

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_rule = request.form['rule']

        if 'excel_file' in request.files:
            excel_file = request.files['excel_file']
            if excel_file.filename != '':
                data = pd.read_excel(excel_file)
            else:
                return render_template('index.html', error_message='Vui lòng chọn một tệp Excel.')

        if selected_rule == '1':
            result = luat_EDD(data)
        elif selected_rule == '2':
            result = luat_MS(data)
        elif selected_rule == '3':
            result = luat_SPT(data)
        elif selected_rule == '4':
            result = luat_WSPT(data)
        elif selected_rule == '5':
            result = luat_WI(data)
        elif selected_rule == '6':
            result = luat_LPT(data)
        else:
            print("Lựa chọn không hợp lệ.")
            return
        gantt_chart, result_df = create_gantt_chart(result)

        return render_template('index.html', result_df=result_df.to_html(classes='table table-bordered table-striped', index=False), gantt_chart=gantt_chart)
    return render_template('index.html')
# 1 EDD Min Lmax
def luat_EDD(data):
# Sắp xếp danh sách công việc theo thứ tự Dj từ nhỏ đến lớn, thời gian tới hạn sớm nhất
    EDD = data.sort_values(by='Dj', ascending=True)
    a=[0]
    sd = 0
    Min_Lmax = 0
    b=list(EDD["Pj"])
    for i in range(len(EDD)-1):
        sd += b[i]
        a.append(sd)
    EDD.insert(2,"Thời gian bắt đầu",a)
    EDD.insert(3,"Thời gian kết thúc",EDD["Thời gian bắt đầu"]+EDD["Pj"])
    Min_Lmax = (EDD["Thời gian kết thúc"]-EDD['Dj']).max()
    EDD = EDD.drop(['Rj', 'Wj'], axis=1)
    print('Hàm mục tiêu Min Lmax là',Min_Lmax)
    print('Kết quả điều độ theo luật EDD')
    return EDD
# 2 MS Min Lmax
# Sắp xếp danh sách công việc có thời gian dư (slack) nhỏ nhất
def luat_MS(data):
    # Tính thời gian dư (dj - pj)
    data['S'] = data['Dj'] - data['Pj']
    # Sắp xếp công việc theo thời gian dư tăng dần
    MS = data.sort_values(by=['S','Pj'], ascending=[True,True])
    a=[0]
    sd = 0
    Min_Lmax = 0
    b=list(MS["Pj"])
    for i in range(len(MS)-1):
        sd += b[i]
        a.append(sd)
    MS.insert(2,"Thời gian bắt đầu",a)
    MS.insert(3,"Thời gian kết thúc",MS["Thời gian bắt đầu"]+MS["Pj"])
    Min_Lmax = (MS["Thời gian kết thúc"]-MS['Dj']).max()
    MS = MS.drop(['Rj', 'Wj'], axis=1)
    print('Hàm mục tiêu Min Lmax là',Min_Lmax)
    print('Kết quả điều độ theo luật MS')
    return MS
# 3 SPT TongCj
def luat_SPT(data):
    SPT = data.sort_values(by='Pj', ascending=True)
    a=[0]
    sd = 0
    Tong_Cj= 0
    b=list(SPT["Pj"])
    for i in range(len(SPT)-1):
        sd += b[i]
        a.append(sd)
    SPT.insert(2,"Thời gian bắt đầu",a)
    SPT.insert(3,"Thời gian kết thúc",SPT["Thời gian bắt đầu"]+SPT["Pj"])
    Tong_Cj = SPT["Thời gian kết thúc"].sum()
    SPT = SPT.drop(['Rj', 'Wj', 'Dj'], axis=1)
    print('Kết quả hàm mục tiêu Min Cj là', Tong_Cj)
    print('Kết quả điều độ theo luật SPT')
    return SPT
# 4 WSPT Thoi gian gia cong ngan nhat co trong so  (tong wjCj)
def luat_WSPT(data):
    # Tính trọng số
    data['Trọng số'] = data['Pj'] / data['Wj']
    # Sắp xếp công việc theo thời gian dư tăng dần
    WSPT = data.sort_values(by='Trọng số', ascending=True)
    a=[0]
    sd = 0
    Tong_WjCj = 0
    b=list(WSPT["Pj"])
    for i in range(len(WSPT)-1):
        sd += b[i]
        a.append(sd)
    WSPT.insert(2,"Thời gian bắt đầu",a)
    WSPT.insert(3,"Thời gian kết thúc",WSPT["Thời gian bắt đầu"]+WSPT["Pj"])
    Tong_WjCj = (WSPT["Thời gian kết thúc"]*WSPT['Wj']).sum()
    WSPT = WSPT.drop(['Rj', 'Wj', 'Dj'], axis=1)
    print('Kết quả hàm mục tiêu Min WjCj là', Tong_WjCj)
    print('Kết quả điều độ theo luật WSPT')
    return WSPT
# 5 WI trọng số lớn nhất
def luat_WI(data):
# Sắp xếp danh sách công việc theo thứ tự Wj từ lớn đến nhỏ
    WI = data.sort_values(by=['Wj', 'Pj'], ascending=[False, True])
    a=[0]
    Tong_WjCj = 0
    sd = 0
    b=list(WI["Pj"])
    for i in range(len(WI)-1):
        sd += b[i]
        a.append(sd)
    WI.insert(2,"Thời gian bắt đầu",a)
    WI.insert(3,"Thời gian kết thúc",WI["Thời gian bắt đầu"]+WI["Pj"])
    Tong_WjCj = (WI["Thời gian kết thúc"]*WI['Wj']).sum()
    WI = WI.drop(['Rj', 'Dj'], axis=1)
    print('Hàm mục tiêu Min Tổng WjCj là',Tong_WjCj)
    print('Kết quả điều độ theo luật WI')
    return WI
# 6 LPT thời gian gia công dài nhất
def luat_LPT(data):
# Sắp xếp danh sách công việc theo thứ tự Wj từ lớn đến nhỏ
    LPT = data.sort_values(by='Pj', ascending=False)
    a=[0]
    sd = 0
    Min_Cmax = 0
    b=list(LPT["Pj"])
    for i in range(len(LPT)-1):
        sd += b[i]
        a.append(sd)
    LPT.insert(2,"Thời gian bắt đầu",a)
    LPT.insert(3,"Thời gian kết thúc",LPT["Thời gian bắt đầu"]+LPT["Pj"])
    Min_Cmax = LPT["Thời gian kết thúc"].max()
    LPT = LPT.drop(['Rj', 'Wj', 'Dj'], axis=1)
    print('Hàm mục tiêu Min Cmax là',Min_Cmax)
    print('Kết quả điều độ theo luật LPT')
    return LPT
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

