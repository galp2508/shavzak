import SwiftUI

struct ContentView: View {
    var body: some View {
        WebView(url:
          Bundle.main.url(
            forResource: "index",
            withExtension: "html",
            subdirectory: "dist")!
            )
            .ignoresSafeArea()
    }
}
