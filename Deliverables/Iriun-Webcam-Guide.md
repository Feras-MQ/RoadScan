# Use your phone as RoadScan's camera

**Goal:** phone camera → Iriun on your computer → RoadScan live recognition. Keep the phone and computer nearby for the first test.

## 1. Get the two Iriun apps

Install **both** the phone app and the computer companion:

| Device | Official download |
| --- | --- |
| Windows, Mac or Linux computer | [Iriun Webcam](https://iriun.com/) — choose your computer's operating system |
| Android phone | [Iriun 4K Webcam on Google Play](https://play.google.com/store/apps/details?id=com.jacksoftw.webcam) — developer **Iriun Oy** |
| iPhone | [Iriun Webcam on the App Store](https://apps.apple.com/us/app/iriun-webcam-for-pc-and-mac/id1439303579) — developer **Iriun Oy** |

As checked on **28 October 2026**, [Iriun's computer page](https://iriun.com/) lists Windows 7 or later, macOS 12.3 or later, and Ubuntu 22.04 or later. The [iPhone listing](https://apps.apple.com/us/app/iriun-webcam-for-pc-and-mac/id1439303579) requires iOS 13 or later; check Google Play on your Android device for compatibility. These are **Iriun requirements**; follow [RoadScan's separate Docker setup](Run-On-Another-Computer.md) for the computer running RoadScan.

## 2. Make the phone picture appear on the computer

1. Connect the phone and computer to the **same Wi-Fi network**.
2. Open **Iriun Webcam** on both devices. Allow the phone app to use the camera; allow local-network access if your phone requests it.
3. Wait until the computer's Iriun window shows the phone's picture. Leave both apps running.

The official [Android](https://play.google.com/store/apps/details?id=com.jacksoftw.webcam) and [iPhone](https://apps.apple.com/us/app/iriun-webcam-for-pc-and-mac/id1439303579) instructions describe launching both apps and connecting automatically over Wi-Fi. This guide uses Wi-Fi.

## 3. Open RoadScan on that computer

1. Start RoadScan using the [run guide](Run-On-Another-Computer.md).
2. Open [RoadScan locally](http://127.0.0.1:8000) in the **computer's browser** and connect your workspace.
3. Confirm a trained detector is loaded. If the interface says no detector is loaded, resolve that in **Settings** first.

Iriun runs on the computer. The browser opens its camera feed and sends image frames to RoadScan in Docker for analysis; Docker does not need direct access to the phone camera.

## 4. Select the phone camera

1. Open **Live recognition / التعرف المباشر**.
2. Set **Source** to **Camera / Iriun / USB**.
3. Under **Camera**, select the entry containing **Iriun**. **Default camera (prefers Iriun)** also works when the browser exposes Iriun's name.
4. Select **Balanced · lighter CPU load** for the first test.
5. Click **Start live recognition / بدء التعرف المباشر** and allow the browser's camera request.

If camera names were hidden before permission, click **Stop recognition**, use the circular-arrow **Refresh cameras** button, select Iriun, and start again.

## 5. Check that analysis is running

Point the phone at a well-lit road image or road surface while stationary. Check that **Frames analyzed** increases and **Latest processed frame** updates.

**No Capture click is needed.** RoadScan analyzes frames automatically, one at a time; speed depends on the model and computer. Boxes belong to the displayed processed frame, which can lag behind the camera preview. No boxes does not prove the road is undamaged.

Keep the RoadScan tab visible: hiding it or leaving this view stops recognition. Use **Stop recognition** when finished; **Use this frame for a report** is a separate, optional step.

## 6. If something does not work

| Problem | Next step |
| --- | --- |
| No phone picture in Iriun | Check both apps are open and both devices share the same Wi-Fi; restart the apps. On a managed or guest network, ask its administrator whether device-to-device connections are allowed. |
| Iriun is missing in RoadScan | Open Iriun first, refresh the browser, then use **Refresh cameras**. Grant camera permission before expecting device names. |
| Camera permission denied or camera busy | Allow camera access for RoadScan in the browser's site settings; check the computer's camera privacy settings. Close other apps using that camera, then retry. |
| Browser says camera access is unavailable | Open RoadScan on the same computer at `http://127.0.0.1:8000`, or use a properly configured HTTPS address. An ordinary HTTP network address may block camera access. |
| Picture works but analysis cannot start | Confirm RoadScan is connected and a detector is loaded. Try **Balanced** and wait for the current frame to finish. |

## 7. Keep a fallback ready

- **Another webcam:** select the built-in or regular USB webcam in the same **Camera** list.
- **Recorded video:** select **Video · real-time preview (samples frames)**, click **Choose video**, and open an MP4 or WebM supported by your browser.
- **Still image:** use **Upload road photo** in the overview with a JPEG, PNG or WebP, then follow the report workflow.

**Verification status:** The maintainer reports that Iriun works on their setup. The interface labels and automatic-frame flow above were checked against the current RoadScan source; a physical phone → Iriun → RoadScan detection test was not performed for this guide. No installer, camera permission, firewall setting or running service was changed during this documentation check.
