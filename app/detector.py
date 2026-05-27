import cv2
import numpy as np

class PeopleDetector:
    """
    Detector leve para servidor.
    Usa HOG para corpo inteiro e Haar Cascade para rostos como apoio.
    Ideal para Railway/plano pequeno.
    """

    def __init__(self):
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        self.face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    def _resize(self, image, max_width=900):
        h, w = image.shape[:2]
        if w <= max_width:
            return image, 1.0
        scale = max_width / float(w)
        new = cv2.resize(image, (int(w * scale), int(h * scale)))
        return new, scale

    def _nms(self, boxes, overlap_thresh=0.35):
        if len(boxes) == 0:
            return []
        boxes_np = np.array(boxes, dtype=float)
        x1 = boxes_np[:,0]
        y1 = boxes_np[:,1]
        x2 = boxes_np[:,0] + boxes_np[:,2]
        y2 = boxes_np[:,1] + boxes_np[:,3]
        area = (x2 - x1 + 1) * (y2 - y1 + 1)
        idxs = np.argsort(y2)
        pick = []
        while len(idxs) > 0:
            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)
            xx1 = np.maximum(x1[i], x1[idxs[:last]])
            yy1 = np.maximum(y1[i], y1[idxs[:last]])
            xx2 = np.minimum(x2[i], x2[idxs[:last]])
            yy2 = np.minimum(y2[i], y2[idxs[:last]])
            w = np.maximum(0, xx2 - xx1 + 1)
            h = np.maximum(0, yy2 - yy1 + 1)
            overlap = (w * h) / area[idxs[:last]]
            idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlap_thresh)[0])))
        return boxes_np[pick].astype(int).tolist()

    def detect(self, image_bgr, mode="body", draw=True):
        original_h, original_w = image_bgr.shape[:2]
        image, scale = self._resize(image_bgr)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        boxes = []

        if mode in ("body", "auto"):
            rects, weights = self.hog.detectMultiScale(
                image,
                winStride=(8, 8),
                padding=(8, 8),
                scale=1.05
            )
            for (x, y, w, h), weight in zip(rects, weights):
                if weight >= 0.35 and w*h > 2500:
                    boxes.append((int(x), int(y), int(w), int(h), float(weight), "pessoa"))

        if mode in ("face", "auto"):
            faces = self.face.detectMultiScale(
                gray,
                scaleFactor=1.08,
                minNeighbors=5,
                minSize=(28, 28)
            )
            for (x, y, w, h) in faces:
                # expande rosto para estimar região da pessoa
                px = max(0, x - int(w*0.8))
                py = max(0, y - int(h*0.7))
                pw = min(image.shape[1] - px, int(w * 2.6))
                ph = min(image.shape[0] - py, int(h * 5.0))
                boxes.append((px, py, pw, ph, 0.5, "rosto"))

        boxes_simple = [(x,y,w,h) for x,y,w,h,conf,label in boxes]
        boxes_simple = self._nms(boxes_simple)

        # volta escala original
        if scale != 1.0:
            inv = 1.0 / scale
            boxes_simple = [(int(x*inv), int(y*inv), int(w*inv), int(h*inv)) for x,y,w,h in boxes_simple]

        annotated = image_bgr.copy()
        if draw:
            for i, (x,y,w,h) in enumerate(boxes_simple, start=1):
                cv2.rectangle(annotated, (x,y), (x+w, y+h), (0, 255, 0), 3)
                cv2.putText(annotated, f"Pessoa {i}", (x, max(25, y-8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2, cv2.LINE_AA)
            cv2.putText(annotated, f"Total: {len(boxes_simple)}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0), 3, cv2.LINE_AA)

        return {
            "count": len(boxes_simple),
            "boxes": [{"x":x, "y":y, "w":w, "h":h} for x,y,w,h in boxes_simple],
            "annotated": annotated
        }

detector = PeopleDetector()