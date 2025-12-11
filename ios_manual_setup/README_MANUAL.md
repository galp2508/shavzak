# 📱 Manual iOS Setup (Ditto Blog Method)

Since you are on Windows, you cannot run Xcode here. However, I have prepared all the files you need to follow the [Ditto Blog Tutorial](https://www.ditto.com/blog/running-a-react-web-app-in-an-ios-app) on a Mac.

## Instructions for Mac

1.  **Create a new iOS App in Xcode**:
    *   Name: `ReactInMobile` (or `ShavzakApp`)
    *   Interface: **SwiftUI**
    *   Language: **Swift**
    *   Place the project folder **next to** the `front` folder (not inside it).

2.  **Add the Swift Files**:
    *   Copy `WebView.swift` from this folder into your Xcode project.
    *   Replace the content of `ContentView.swift` in Xcode with the content of `ContentView.swift` from this folder.

3.  **Add the Build Script**:
    *   In Xcode, click on your project target.
    *   Go to **Build Phases**.
    *   Click **+** -> **New Run Script Phase**.
    *   Drag it **above** "Compile Sources".
    *   Paste the content of `xcode_build_script.sh` into the script box.
    *   *Note*: The script assumes your React folder is named `front` and is located one level up (`../front`).

4.  **Add Bundle Resources**:
    *   In **Build Phases**, find **Copy Bundle Resources**.
    *   Click **+** -> **Add Other...**.
    *   Navigate to `front/dist` (you might need to run `npm run build` in `front` first to create it).
    *   **Important**: Select "Create folder references" (blue folder icon), NOT "Create groups".

5.  **Run**:
    *   Press Play in Xcode to run on Simulator or Device.

---

## Alternative: Capacitor (Recommended)
I have also set up **Capacitor** in the `front` folder. This is the modern, automated way to do exactly what the blog post describes manually.

To use Capacitor (on Mac):
1.  `cd front`
2.  `npx cap add ios`
3.  `npx cap open ios`
4.  Run in Xcode.

This handles the WebView, plugins, and assets automatically.
