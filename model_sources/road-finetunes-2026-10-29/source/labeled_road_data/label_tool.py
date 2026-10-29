# SPDX-License-Identifier: AGPL-3.0-only
# Scope: this team contribution; see the accompanying NOTICE.md.
"""Minimal box labeling app for video_dataset/<split> (YOLO format, saved in place).

    python label_tool.py            # label the test frames (do these first: they give the real road score)
    python label_tool.py train      # label the training frames

Mouse: drag = new box (current class) | click a box = set it to current class | right-click a box = delete
Keys:  0-4 = current class | N/Space = next | P = previous | U = undo | X = no damage (clear frame) | Q/Esc = save + quit
Every frame you leave is saved and marked reviewed (reviewed.txt), so the next start resumes where you stopped.
"""
import sys
from pathlib import Path

import cv2

NAMES = ["D00 Longitudinal", "D10 Transverse", "D20 Alligator", "Other (patch/marking)", "D40 Pothole"]
COLORS = [(255, 80, 0), (0, 200, 255), (0, 220, 0), (200, 0, 200), (0, 0, 255)]
MAX_W, MAX_H = 1600, 900


def load_boxes(path: Path, w: int, h: int) -> list[list]:
    """YOLO txt -> [[cls, x1, y1, x2, y2], ...] in pixels."""
    boxes = []
    if path.exists():
        for line in path.read_text().split("\n"):
            if line.strip():
                c, x, y, bw, bh = line.split()
                x, y, bw, bh = float(x) * w, float(y) * h, float(bw) * w, float(bh) * h
                boxes.append([int(c), x - bw / 2, y - bh / 2, x + bw / 2, y + bh / 2])
    return boxes


def save_boxes(path: Path, boxes: list[list], w: int, h: int) -> None:
    path.write_text("".join(
        f"{c} {(x1 + x2) / 2 / w:.6f} {(y1 + y2) / 2 / h:.6f} {(x2 - x1) / w:.6f} {(y2 - y1) / h:.6f}\n"
        for c, x1, y1, x2, y2 in boxes))


def box_at(boxes: list[list], x: float, y: float):
    """Smallest box containing the point, so nested boxes stay reachable."""
    hits = [b for b in boxes if b[1] <= x <= b[3] and b[2] <= y <= b[4]]
    return min(hits, key=lambda b: (b[3] - b[1]) * (b[4] - b[2])) if hits else None


def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 else "test"
    root = Path(__file__).resolve().parent / "video_dataset" / split
    images = sorted((root / "images").glob("*.jpg"))
    if not images:
        raise SystemExit(f"No images in {root / 'images'}")
    done_file = root / "reviewed.txt"
    reviewed = set(done_file.read_text().split()) if done_file.exists() else set()
    idx = next((i for i, p in enumerate(images) if p.stem not in reviewed), 0)
    state = {"cls": 0, "drag": None, "mouse": (0, 0)}

    def open_frame(i):
        img = cv2.imread(str(images[i]))
        h, w = img.shape[:2]
        scale = min(MAX_W / w, MAX_H / h)
        return img, w, h, scale, load_boxes(root / "labels" / f"{images[i].stem}.txt", w, h)

    img, w, h, scale, boxes = open_frame(idx)
    history = []

    def on_mouse(event, mx, my, flags, _):
        x, y = mx / scale, my / scale
        state["mouse"] = (x, y)
        if event == cv2.EVENT_LBUTTONDOWN:
            state["drag"] = (x, y)
        elif event == cv2.EVENT_LBUTTONUP and state["drag"]:
            x0, y0 = state["drag"]
            state["drag"] = None
            history.append([b[:] for b in boxes])
            if abs(x - x0) * scale > 5 and abs(y - y0) * scale > 5:
                boxes.append([state["cls"], max(0, min(x0, x)), max(0, min(y0, y)), min(w, max(x0, x)), min(h, max(y0, y))])
            elif (b := box_at(boxes, x, y)) is not None:
                b[0] = state["cls"]
            else:
                history.pop()
        elif event == cv2.EVENT_RBUTTONDOWN and (b := box_at(boxes, x, y)) is not None:
            history.append([b[:] for b in boxes])
            boxes.remove(b)

    win = "RoadScan labeler"
    cv2.namedWindow(win)
    cv2.setMouseCallback(win, on_mouse)
    while True:
        view = cv2.resize(img, (int(w * scale), int(h * scale)))
        for c, x1, y1, x2, y2 in boxes:
            p1, p2 = (int(x1 * scale), int(y1 * scale)), (int(x2 * scale), int(y2 * scale))
            cv2.rectangle(view, p1, p2, COLORS[c], 2)
            cv2.putText(view, NAMES[c], (p1[0], max(15, p1[1] - 5)), 0, 0.55, COLORS[c], 2)
        if state["drag"]:
            (x0, y0), (x, y) = state["drag"], state["mouse"]
            cv2.rectangle(view, (int(x0 * scale), int(y0 * scale)), (int(x * scale), int(y * scale)), COLORS[state["cls"]], 1)
        status = (f"{split} {idx + 1}/{len(images)} {images[idx].stem} | reviewed {len(reviewed)} | "
                  f"class [{state['cls']}] {NAMES[state['cls']]} | N next  P prev  U undo  X no-damage  Q quit")
        cv2.rectangle(view, (0, 0), (view.shape[1], 28), (0, 0, 0), -1)
        cv2.putText(view, status, (8, 20), 0, 0.55, (255, 255, 255), 1)
        cv2.imshow(win, view)
        key = cv2.waitKey(20) & 0xFF
        if cv2.getWindowProperty(win, cv2.WND_PROP_VISIBLE) < 1:
            key = ord("q")  # window closed with the X button: still save
        if ord("0") <= key <= ord("4"):
            state["cls"] = key - ord("0")
        elif key == ord("u") and history:
            boxes[:] = history.pop()
        elif key == ord("x"):
            history.append([b[:] for b in boxes])
            boxes.clear()
        elif key in (ord("n"), ord(" "), ord("p"), ord("q"), 27):
            save_boxes(root / "labels" / f"{images[idx].stem}.txt", boxes, w, h)
            reviewed.add(images[idx].stem)
            done_file.write_text("\n".join(sorted(reviewed)) + "\n")
            if key in (ord("q"), 27):
                break
            idx = min(idx + 1, len(images) - 1) if key in (ord("n"), ord(" ")) else max(idx - 1, 0)
            img, w, h, scale, boxes = open_frame(idx)
            history.clear()
    cv2.destroyAllWindows()
    print(f"Saved. Reviewed {len(reviewed)}/{len(images)} {split} frames.")


if __name__ == "__main__":
    main()
