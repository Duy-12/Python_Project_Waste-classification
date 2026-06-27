import os
import sys

# Chuẩn hóa stdout để tránh lỗi mã hóa trên Windows console
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def resolve_path(base_dir, path):
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(base_dir, path))


def list_image_files(folder):
    extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    return sorted([entry for entry in os.listdir(folder) if entry.lower().endswith(extensions)])


def list_label_files(folder):
    return sorted([entry for entry in os.listdir(folder) if entry.lower().endswith('.txt')])


def load_data_yaml(yaml_path):
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Không tìm thấy file: {yaml_path}")

    train_dir = None
    val_dir = None
    with open(yaml_path, 'r', encoding='utf-8') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            if line.lower().startswith('train:'):
                train_dir = resolve_path(os.path.dirname(yaml_path), line.split(':', 1)[1].strip())
            elif line.lower().startswith('val:'):
                val_dir = resolve_path(os.path.dirname(yaml_path), line.split(':', 1)[1].strip())
    return train_dir, val_dir


def validate_folders(train_dir, val_dir):
    messages = []
    if not os.path.isdir(train_dir):
        messages.append(f"Thư mục train không tồn tại: {train_dir}")
    if not os.path.isdir(val_dir):
        messages.append(f"Thư mục val không tồn tại: {val_dir}")
    return messages


def validate_files(train_dir, val_dir):
    messages = []
    train_images = list_image_files(train_dir)
    val_images = list_image_files(val_dir)

    if not train_images:
        messages.append(f"Không có ảnh trong train/images ({train_dir})")
    if not val_images:
        messages.append(f"Không có ảnh trong val/images ({val_dir})")

    train_labels_dir = os.path.join(os.path.dirname(train_dir), 'labels')
    val_labels_dir = os.path.join(os.path.dirname(val_dir), 'labels')

    if not os.path.isdir(train_labels_dir):
        messages.append(f"Thư mục label train không tồn tại: {train_labels_dir}")
    if not os.path.isdir(val_labels_dir):
        messages.append(f"Thư mục label val không tồn tại: {val_labels_dir}")

    if os.path.isdir(train_labels_dir):
        train_labels = list_label_files(train_labels_dir)
        missing = [img for img in train_images if f"{os.path.splitext(img)[0]}.txt" not in train_labels]
        if missing:
            messages.append(f"Ảnh train chưa có nhãn: {missing[:10]}{'...' if len(missing) > 10 else ''}")
        empty = [label for label in train_labels if os.path.getsize(os.path.join(train_labels_dir, label)) == 0]
        if empty:
            messages.append(f"File label train rỗng: {empty[:10]}{'...' if len(empty) > 10 else ''}")
    if os.path.isdir(val_labels_dir):
        val_labels = list_label_files(val_labels_dir)
        missing = [img for img in val_images if f"{os.path.splitext(img)[0]}.txt" not in val_labels]
        if missing:
            messages.append(f"Ảnh val chưa có nhãn: {missing[:10]}{'...' if len(missing) > 10 else ''}")
        empty = [label for label in val_labels if os.path.getsize(os.path.join(val_labels_dir, label)) == 0]
        if empty:
            messages.append(f"File label val rỗng: {empty[:10]}{'...' if len(empty) > 10 else ''}")

    return messages


def summarize(train_dir, val_dir):
    train_images = list_image_files(train_dir)
    val_images = list_image_files(val_dir)
    train_labels = list_label_files(os.path.join(os.path.dirname(train_dir), 'labels'))
    val_labels = list_label_files(os.path.join(os.path.dirname(val_dir), 'labels'))

    return {
        'train_images': len(train_images),
        'train_labels': len(train_labels),
        'val_images': len(val_images),
        'val_labels': len(val_labels),
    }


def main():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    yaml_path = os.path.join(current_dir, 'data.yaml')
    print('=' * 60)
    print('KIỂM TRA DỮ LIỆU HUẤN LUYỆN YOLO')
    print('=' * 60)

    try:
        train_dir, val_dir = load_data_yaml(yaml_path)
    except FileNotFoundError as e:
        print(f"[LỖI] {e}")
        return

    if not train_dir or not val_dir:
        print('[LỖI] File data.yaml phải khai báo đầy đủ train và val.')
        return

    errors = validate_folders(train_dir, val_dir)
    if not errors:
        errors.extend(validate_files(train_dir, val_dir))

    if errors:
        print('[KẾT QUẢ] Dataset chưa hợp lệ:')
        for msg in errors:
            print(f' - {msg}')
        print('\nHướng dẫn:')
        print('  1. Put image files into dataset/train/images and dataset/val/images')
        print('  2. Put corresponding YOLO label files into dataset/train/labels and dataset/val/labels')
        print('  3. Labels filenames must match image filenames, e.g. image.jpg -> image.txt')
        print('  4. Label format: class x_center y_center width height (normalized)')
        return

    summary = summarize(train_dir, val_dir)
    print('[KẾT QUẢ] Dataset hợp lệ:')
    print(f"  - train images: {summary['train_images']}")
    print(f"  - train labels: {summary['train_labels']}")
    print(f"  - val images: {summary['val_images']}")
    print(f"  - val labels: {summary['val_labels']}")
    print('Bạn có thể chạy AI_Service/train_and_export.py để huấn luyện model.')


if __name__ == '__main__':
    main()
