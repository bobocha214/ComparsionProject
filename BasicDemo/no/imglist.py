import tkinter as tk
from tkinter import Scrollbar, Listbox, Button, messagebox
import os

# 创建主窗口
root = tk.Tk()
root.title("显示图片文件列表")

# 指定文件夹路径
folder_path = "../image"  # 替换成您的文件夹路径

# 创建列表框
listbox = Listbox(root, width=40, height=10)
listbox.pack(padx=20, pady=20)

# 创建滚动条
scrollbar = Scrollbar(root, command=listbox.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
listbox.config(yscrollcommand=scrollbar.set)

# 获取文件夹中的图片文件列表
image_files = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]

# 将图片文件名添加到列表框中
for file in image_files:
    listbox.insert(tk.END, file)

# 创建查看按钮
def view_image():
    selected_item = listbox.get(listbox.curselection())
    if selected_item:
        file_path = os.path.join(folder_path, selected_item)
        # 在这里执行查看文件的操作，比如显示图像
        # 您可以使用Pillow或其他图像库来显示图像

view_button = Button(root, text="查看", command=view_image)
view_button.pack()

# 创建删除按钮
def delete_image():
    selected_indices = listbox.curselection()
    if selected_indices:
        selected_item = listbox.get(selected_indices[0])  # 获取第一个选定的项目
        file_path = os.path.join(folder_path, selected_item)
        try:
            os.remove(file_path)
            listbox.delete(selected_indices)  # 从列表框中删除选定的项目
            messagebox.showinfo("删除成功", f"文件 {selected_item} 已删除")
        except Exception as e:
            messagebox.showerror("删除失败", f"无法删除文件 {selected_item}: {str(e)}")

delete_button = Button(root, text="删除", command=delete_image)
delete_button.pack()

# 启动Tkinter事件循环
root.mainloop()
