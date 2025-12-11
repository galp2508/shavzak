# This will clear the dist directory in the iOS app if there is one from a previous build
rm -rf "${BUILT_PRODUCTS_DIR}/${PRODUCT_NAME}.app/dist"

# This will use nvm to install Node.js v20 and use it to build the web app
# If Node.js 20 is already installed, it will use that
export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
  . "$NVM_DIR/nvm.sh"
  nvm install 20
  nvm use 20
else
  # If nvm is not available, use the system-installed node
  export PATH="/usr/local/bin:$PATH"
fi

# This script will go up a directory to find the web app
# NOTE: We use 'front' instead of 'web' as per your project structure
cd ../front

# This will install the dependencies for the web app (if they are not already installed)
npm install

# This will build the web app
npm run build
