import customtkinter as ctk
from tkinter import ttk  # Dùng để vẽ bảng hiển thị danh sách lịch sử
from PIL import Image
import os
import sqlite3

class DataFrameView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f8f9fa")
        
        # Cấu hình Layout lưới Grid
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(2, weight=1)

        # --- ĐƯỜNG DẪN DATABASE ---
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.normpath(os.path.join(current_dir, "..", "Backend", "history_database.db"))

        # --- LOAD ICON CHO NÚT BẤM VÀ THÔNG BÁO TRỐNG ---
        logo_path = os.path.join(current_dir, "logo")
        try:
            self.icon_export = ctk.CTkImage(light_image=Image.open(os.path.join(logo_path, "export_white.png")), size=(18, 18))
            self.icon_delete = ctk.CTkImage(light_image=Image.open(os.path.join(logo_path, "delete_white.png")), size=(18, 18))
            self.img_empty_hist = ctk.CTkImage(light_image=Image.open(os.path.join(logo_path, "empty_history.png")), size=(64, 64))
            self.img_empty_det = ctk.CTkImage(light_image=Image.open(os.path.join(logo_path, "empty_detail.png")), size=(64, 64))
        except Exception as e:
            self.icon_export = self.icon_delete = self.img_empty_hist = self.img_empty_det = None

        # 1. PHẦN TIÊU ĐỀ - ĐÃ CĂN GIỮA THEO ĐÚNG Ý BẠN
        self.header_section = ctk.CTkFrame(self, fg_color="transparent")
        self.header_section.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(self.header_section, text="Quản Lý Dữ Liệu", font=("Arial", 34, "bold"), text_color="black").pack(anchor="center")
        ctk.CTkLabel(self.header_section, text="Xem lại lịch sử phân tích và thống kê", font=("Arial", 17), text_color="gray").pack(anchor="center", pady=(5, 0))

        # 2. KHUNG 4 THẺ THỐNG KÊ
        self.top_cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_cards_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 25))
        for i in range(4): self.top_cards_frame.grid_columnconfigure(i, weight=1)

        colors = ["#00a843", "#1b66ff", "#dca100", "#e61224"]
        titles = ["Hữu Cơ", "Vô Cơ", "Tái Chế", "Độc Hại"]
        self.card_labels = {} 

        for i in range(4):
            card = ctk.CTkFrame(self.top_cards_frame, fg_color=colors[i], height=135, corner_radius=12)
            card.grid(row=0, column=i, padx=8, sticky="ew")
            card.pack_propagate(False)
            
            ctk.CTkLabel(card, text=titles[i], font=("Arial", 19, "bold"), text_color="white").pack(anchor="w", padx=20, pady=(15, 2))
            
            lbl_count = ctk.CTkLabel(card, text="0", font=("Arial", 40, "bold"), text_color="white")
            lbl_count.pack(anchor="w", padx=20)
            self.card_labels[titles[i]] = lbl_count 
            
            ctk.CTkLabel(card, text="vật thể phát hiện", font=("Arial", 15), text_color="#ffffff").pack(anchor="w", padx=20)

        # 3. KHUNG LỊCH SỬ PHÂN TÍCH (Bên trái)
        self.history_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="white", border_color="#eaedf0", border_width=1)
        self.history_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 10))
        
        self.header_hist = ctk.CTkFrame(self.history_frame, fg_color="transparent", height=70)
        self.header_hist.pack(fill="x", padx=22, pady=(10, 5))
        self.header_hist.pack_propagate(False)
        
        self.lbl_hist_title = ctk.CTkLabel(self.header_hist, text="Lịch Sử Phân Tích (0)", font=("Arial", 22, "bold"), text_color="black")
        self.lbl_hist_title.pack(side="left")
        
        ctk.CTkButton(self.header_hist, text=" Xóa Tất Cả", image=self.icon_delete, compound="left", width=130, height=38, fg_color="#ff4d6d", hover_color="#ff1a43", text_color="white", font=("Arial", 14, "bold"), corner_radius=8, command=self.clear_all_data).pack(side="right", padx=5)
        ctk.CTkButton(self.header_hist, text=" Xuất", image=self.icon_export, compound="left", width=100, height=38, fg_color="#4cc9f0", hover_color="#4361ee", text_color="white", font=("Arial", 14, "bold"), corner_radius=8, command=self.export_to_csv).pack(side="right", padx=5)
        self.filter_buttons_frame = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        self.filter_buttons_frame.pack(fill="x", padx=22, pady=(0, 10))
        
        self.filter_btns = {}
        options = ["Tất cả", "Rác hữu cơ", "Rác vô cơ", "Rác tái chế", "Rác độc hại"]
        for opt in options:
            btn = ctk.CTkButton(self.filter_buttons_frame, text=opt, width=90, height=30, 
                                fg_color="#e0e0e0", text_color="black", font=("Arial", 12),
                                command=lambda o=opt: self.filter_data(o))
            btn.pack(side="left", padx=5)
            self.filter_btns[opt] = btn
        ctk.CTkFrame(self.history_frame, height=2, fg_color="#eaedf0").pack(fill="x", padx=22, pady=(5, 10))
        
        # VÙNG CHỨA NỘI DUNG LỊCH SỬ ĐỘNG
        self.hist_content_area = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        self.hist_content_area.pack(fill="both", expand=True)

        self.table_frame = ctk.CTkFrame(self.hist_content_area, fg_color="transparent")
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=35, font=("Arial", 13), background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Arial", 14, "bold"), background="#f0f2f5", foreground="black")
        
        self.tree = ttk.Treeview(self.table_frame, columns=("STT", "Thời Gian", "Loại Rác", "Độ Tin Cậy"), show="headings")
        self.tree.heading("STT", text="STT")
        self.tree.heading("Thời Gian", text="Thời Gian")
        self.tree.heading("Loại Rác", text="Loại Rác")
        self.tree.heading("Độ Tin Cậy", text="Độ Tin Cậy")
        
        self.tree.column("STT", width=60, anchor="center")
        self.tree.column("Thời Gian", width=220, anchor="center")
        self.tree.column("Loại Rác", width=150, anchor="center")
        self.tree.column("Độ Tin Cậy", width=120, anchor="center")
        
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_row_selected)

        # 4. KHUNG CHI TIẾT (Bên phải)
        self.detail_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="white", border_color="#eaedf0", border_width=1)
        self.detail_frame.grid(row=2, column=1, sticky="nsew", padx=(10, 0))
        
        self.header_det = ctk.CTkFrame(self.detail_frame, fg_color="transparent", height=70)
        self.header_det.pack(fill="x", padx=22, pady=(10, 5))
        self.header_det.pack_propagate(False)
        ctk.CTkLabel(self.header_det, text="Chi Tiết", font=("Arial", 22, "bold"), text_color="black").pack(side="left")
        ctk.CTkFrame(self.detail_frame, height=2, fg_color="#eaedf0").pack(fill="x", padx=22, pady=(5, 10))
        
        # ĐÃ ĐỔI THÀNH CTkScrollableFrame: Thêm thanh cuộn tự động khi thu nhỏ màn hình
        self.detail_content_area = ctk.CTkScrollableFrame(self.detail_frame, fg_color="transparent", label_text="")
        self.detail_content_area.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        
        self.show_empty_detail_state()

        # TỰ ĐỘNG KIỂM TRA DATABASE KHI MỞ APP
        self.load_data_from_database()

    def show_empty_history_state(self):
        self.table_frame.pack_forget() 
        for widget in self.hist_content_area.winfo_children():
            if widget != self.table_frame:
                widget.destroy()
                
        empty_hist_center = ctk.CTkFrame(self.hist_content_area, fg_color="transparent")
        empty_hist_center.pack(expand=True)
        if self.img_empty_hist:
            ctk.CTkLabel(empty_hist_center, text="", image=self.img_empty_hist).pack(pady=(0, 15))
        ctk.CTkLabel(empty_hist_center, text="Chưa có dữ liệu phân tích nào", text_color="#a0a5aa", font=("Arial", 17, "bold")).pack()

    def show_empty_detail_state(self):
        for widget in self.detail_content_area.winfo_children():
            widget.destroy()
        empty_det_center = ctk.CTkFrame(self.detail_content_area, fg_color="transparent")
        empty_det_center.pack(expand=True, pady=100) # Thêm khoảng đệm giữa để icon căn giữa khung cuộn
        if self.img_empty_det:
            ctk.CTkLabel(empty_det_center, text="", image=self.img_empty_det).pack(pady=(0, 15))
        ctk.CTkLabel(empty_det_center, text="Chọn một mục để xem chi tiết", text_color="#a0a5aa", font=("Arial", 17, "bold")).pack()

    # ==========================================
    # ĐỌC DỮ LIỆU TỪ BẢNG waste_history
    # ==========================================
    def load_data_from_database(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if not os.path.exists(self.db_path):
            self.show_empty_history_state()
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='waste_history'")
            if not cursor.fetchone():
                self.show_empty_history_state()
                conn.close()
                return

            cursor.execute("SELECT timestamp, label, confidence, image_path FROM waste_history ORDER BY id DESC")
            rows = cursor.fetchall()
            
            if len(rows) == 0:
                self.show_empty_history_state()
            else:
                for widget in self.hist_content_area.winfo_children():
                    if widget != self.table_frame:
                        widget.destroy()
                
                self.table_frame.pack(fill="both", expand=True, padx=22, pady=10)
                
                for stt, row in enumerate(rows, start=1):
                    timestamp, label, confidence, image_path = row
                    
                    try:
                        conf_val = float(confidence)
                        if conf_val <= 1.0:
                            conf_str = f"{conf_val * 100:.1f}%"
                        else:
                            conf_str = f"{conf_val:.1f}%"
                    except ValueError:
                        conf_str = str(confidence)
                        
                    self.tree.insert("", "end", values=(stt, timestamp, label, conf_str, image_path))
            
            self.lbl_hist_title.configure(text=f"Lịch Sử Phân Tích ({len(rows)})")
            
            db_keywords = ["Rác hữu cơ", "Rác vô cơ", "Rác tái chế", "Rác độc hại"]
            ui_titles = ["Hữu Cơ", "Vô Cơ", "Tái Chế", "Độc Hại"]
            
            for keyword, ui_title in zip(db_keywords, ui_titles):
                cursor.execute("SELECT COUNT(*) FROM waste_history WHERE label = ?", (keyword,))
                count = cursor.fetchone()[0]
                self.card_labels[ui_title].configure(text=str(count))
                
            conn.close()
        except Exception as e:
            print(f"Lỗi truy vấn cơ sở dữ liệu: {e}")
            self.show_empty_history_state()

    # ==========================================
    # HIỂN THỊ CHI TIẾT KÈM ẢNH PHÓNG TO & NÚT SỬA NHÃN RÁC
    # ==========================================
    def on_row_selected(self, event):
        selected_item = self.tree.selection()
        if not selected_item: return
            
        item_data = self.tree.item(selected_item[0])["values"]
        _, timestamp, label, conf_str, image_path = item_data
        
        for widget in self.detail_content_area.winfo_children():
            widget.destroy()
            
        info_box = ctk.CTkFrame(self.detail_content_area, fg_color="transparent")
        info_box.pack(fill="both", expand=True, padx=15, pady=10)
        
        label_color_map = {
            "Rác hữu cơ": "#00a843",
            "Rác vô cơ": "#1b66ff",
            "Rác tái chế": "#dca100",
            "Rác độc hại": "#e61224"
        }
        current_text_color = label_color_map.get(label, "#1b66ff")
        
        # Phần hiển thị thông tin dạng chữ
        ctk.CTkLabel(info_box, text="THÔNG TIN PHÂN TÍCH", font=("Arial", 18, "bold"), text_color=current_text_color).pack(anchor="w", pady=(0, 15))
        ctk.CTkLabel(info_box, text=f"• Thời gian quét:", font=("Arial", 15, "bold"), text_color="black").pack(anchor="w", pady=2)
        ctk.CTkLabel(info_box, text=f"  {timestamp}", font=("Arial", 15), text_color="gray").pack(anchor="w", pady=(0, 10))
        ctk.CTkLabel(info_box, text=f"• Kết quả phân loại:", font=("Arial", 15, "bold"), text_color="black").pack(anchor="w", pady=2)
        ctk.CTkLabel(info_box, text=f"  {label}", font=("Arial", 16, "bold"), text_color=current_text_color).pack(anchor="w", pady=(0, 5))
        
        # 🔥 TÍCH HỢP THÊM NÚT "CHỈNH LOẠI RÁC" NGAY DƯỚI CHỮ KẾT QUẢ PHÂN LOẠI
        self.btn_edit_label = ctk.CTkButton(
            info_box,
            text="Chỉnh loại rác",
            fg_color="#ffc107",   # Màu vàng chuẩn công cụ
            text_color="black",
            hover_color="#e0a800",
            font=("Arial", 12, "bold"),
            width=110,
            height=28,
            corner_radius=6,
            command=lambda: self.open_edit_label_window(timestamp, label)
        )
        self.btn_edit_label.pack(anchor="w", pady=(0, 10), padx=5)

        ctk.CTkLabel(info_box, text=f"• Độ tin cậy thuật toán:", font=("Arial", 15, "bold"), text_color="black").pack(anchor="w", pady=2)
        ctk.CTkLabel(info_box, text=f"  {conf_str}", font=("Arial", 15), text_color="gray").pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(info_box, text="• Hình ảnh minh họa:", font=("Arial", 15, "bold"), text_color="black").pack(anchor="w", pady=(0, 5))
        
        img_container = ctk.CTkFrame(info_box, fg_color="#f1f3f5", border_color="#eaedf0", border_width=1, corner_radius=10, height=310)
        img_container.pack(fill="x", pady=5)
        img_container.pack_propagate(False)
        
        backend_dir = os.path.dirname(self.db_path)
        
        if image_path:
            clean_path = str(image_path).replace('/', os.sep).replace('\\', os.sep)
            full_img_path = os.path.normpath(os.path.join(backend_dir, clean_path))
        else:
            full_img_path = ""
        
        if full_img_path and os.path.exists(full_img_path):
            try:
                pil_img = Image.open(full_img_path)
                max_w, max_h = 380, 280  
                orig_w, orig_h = pil_img.size
                
                ratio = min(max_w / orig_w, max_h / orig_h)
                new_w = int(orig_w * ratio)
                new_h = int(orig_h * ratio)
                
                ctk_waste_img = ctk.CTkImage(light_image=pil_img, size=(new_w, new_h))
                
                lbl_img = ctk.CTkLabel(img_container, text="", image=ctk_waste_img)
                lbl_img.image = ctk_waste_img  
                lbl_img.pack(expand=True)
            except Exception as e:
                ctk.CTkLabel(img_container, text=f"Lỗi đọc tập tin ảnh:\n{e}", text_color="red", font=("Arial", 13)).pack(expand=True)
        else:
            ctk.CTkLabel(img_container, text="Không tìm thấy file ảnh\n(Đã bị xóa hoặc chưa lưu)", text_color="#a0a5aa", font=("Arial", 13, "italic")).pack(expand=True)

    # ==========================================
    # CỬA SỔ PHỤ ĐỂ CHỈNH SỬA LOẠI RÁC (4 NHÃN CHUẨN)
    # ==========================================
    def open_edit_label_window(self, current_timestamp, current_label):
        """Mở bảng mini chứa Combobox 4 loại rác khi nhấn nút Chỉnh loại rác"""
        edit_win = ctk.CTkToplevel(self)
        edit_win.title("Chỉnh sửa danh mục rác")
        edit_win.geometry("320x180")
        edit_win.resizable(False, False)
        edit_win.grab_set()  # Khóa tương tác màn hình chính
        
        # Căn giữa cửa sổ mini trên màn hình máy tính
        edit_win.update_idletasks()
        x = (edit_win.winfo_screenwidth() // 2) - (320 // 2)
        y = (edit_win.winfo_screenheight() // 2) - (180 // 2)
        edit_win.geometry(f"+{x}+{y}")

        # Giao diện chữ hướng dẫn bên trong cửa sổ mini
        lbl_info = ctk.CTkLabel(edit_win, text="Chọn lại danh mục phân loại rác chính xác:", font=("Arial", 13))
        lbl_info.pack(pady=(20, 10))

        # Đúng 4 loại rác chuẩn trong đồ án của bạn
        categories = ["Rác hữu cơ", "Rác vô cơ", "Rác tái chế", "Rác độc hại"]
        cb_categories = ctk.CTkComboBox(edit_win, values=categories, width=220, state="readonly")
        cb_categories.pack(pady=5)
        
        # Đặt sẵn giá trị hiện tại cho Combobox
        if current_label in categories:
            cb_categories.set(current_label)
        else:
            cb_categories.set(categories[0])

        def save_new_label():
            """Hàm cập nhật SQLite ngầm và cập nhật đồng bộ UI"""
            new_selected_label = cb_categories.get()
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                # Update dựa theo mốc thời gian duy nhất của bản ghi quét
                cursor.execute("UPDATE waste_history SET label = ? WHERE timestamp = ?", (new_selected_label, current_timestamp))
                conn.commit()
                conn.close()

                edit_win.destroy() # Tắt cửa sổ mini
                
                # Gọi lại hàm tải dữ liệu gốc để làm mới bảng và cập nhật lại 4 thẻ thống kê
                self.load_data_from_database()
                
                # Tìm dòng vừa chỉnh sửa trong bảng và tự động chọn lại nó để làm mới luôn khung Chi Tiết bên phải
                for item in self.tree.get_children():
                    if self.tree.item(item)["values"][1] == current_timestamp:
                        self.tree.selection_set(item)
                        break
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Lỗi hệ thống", f"Không thể cập nhật danh mục dữ liệu: {e}")

        # Nút xác nhận lưu thay đổi
        btn_confirm = ctk.CTkButton(
            edit_win, text="Xác nhận đổi", fg_color="#1b66ff", hover_color="#1553d1",
            width=120, height=32, font=("Arial", 12, "bold"), command=save_new_label
        )
        btn_confirm.pack(pady=(20, 10))

    def clear_all_data(self):
        if not os.path.exists(self.db_path): return
        
        from tkinter import messagebox
        if not messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa TOÀN BỘ dữ liệu lịch sử và ảnh phân tích không?"):
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT image_path FROM waste_history")
            images_to_delete = cursor.fetchall()
            
            backend_dir = os.path.dirname(self.db_path)
            for img_row in images_to_delete:
                if img_row[0]:
                    clean_path = str(img_row[0]).replace('/', os.sep).replace('\\', os.sep)
                    full_p = os.path.join(backend_dir, clean_path)
                    if os.path.exists(full_p):
                        try: os.remove(full_p)
                        except: pass

            cursor.execute("DELETE FROM waste_history")
            conn.commit()
            conn.close()
            
            self.load_data_from_database()
            self.show_empty_detail_state()
            messagebox.showinfo("Thành công", "Đã dọn dẹp sạch sẽ cơ sở dữ liệu và thư mục hình ảnh!")
        except Exception as e:
            print(f"Lỗi khi xóa bảng dữ liệu: {e}")
    
    def export_to_csv(self):
        if not os.path.exists(self.db_path): return
        
        import csv
        from tkinter import filedialog, messagebox
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, timestamp, label, confidence FROM waste_history ORDER BY id ASC")
            rows = cursor.fetchall()
            conn.close()
            
            if len(rows) == 0:
                messagebox.showwarning("Thông báo", "Hiện tại chưa có dữ liệu nào để xuất file!")
                return
                
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
                title="Chọn nơi lưu file báo cáo",
                initialfile="Bao_Cao_Lich_Su_Phan_Loai_Rac.csv"
            )
            
            if not file_path: return 
            
            with open(file_path, mode="w", encoding="utf-8-sig", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["STT", "Thời Gian Quét", "Loại Rác Phát Hiện", "Độ Tin Cậy"])
                for row in rows:
                    try:
                        conf_val = float(row[3])
                        conf_str = f"{conf_val * 100:.1f}%" if conf_val <= 1.0 else f"{conf_val:.1f}%"
                    except ValueError:
                        conf_str = str(row[3])
                        
                    writer.writerow([row[0], row[1], row[2], conf_str])
                    
            messagebox.showinfo("Thành công", "Đã xuất file báo cáo lịch sử thành công!")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất file: {e}")

    def filter_data(self, filter_type):
        # 1. Đổi màu nút đang chọn (highlight)
        for name, btn in self.filter_btns.items():
            if name == filter_type:
                btn.configure(fg_color="#1b66ff", text_color="white") # Màu xanh dương khi chọn
            else:
                btn.configure(fg_color="#e0e0e0", text_color="black") # Màu xám cho nút khác

        # 2. Xóa dữ liệu cũ trong bảng
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 3. Lọc dữ liệu từ DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if filter_type == "Tất cả":
            cursor.execute("SELECT timestamp, label, confidence, image_path FROM waste_history ORDER BY id DESC")
        else:
            cursor.execute("SELECT timestamp, label, confidence, image_path FROM waste_history WHERE label = ? ORDER BY id DESC", (filter_type,))
        
        rows = cursor.fetchall()
        
        # 4. Hiển thị lại
        for stt, row in enumerate(rows, start=1):
            ts, label, conf, img = row
            try:
                conf_str = f"{float(conf)*100:.1f}%" if float(conf) <= 1.0 else f"{float(conf):.1f}%"
            except: conf_str = str(conf)
            self.tree.insert("", "end", values=(stt, ts, label, conf_str, img))
            
        self.lbl_hist_title.configure(text=f"Lịch Sử Phân Tích ({len(rows)})")
        conn.close()