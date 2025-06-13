from ultralytics import YOLO

model = YOLO('runs/detect/train/weights/last.pt')

result = model.train(resume=True)