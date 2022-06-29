if [ -d "./build/" ]; then
    rm -r build
fi
npm run build

if [ -d "../dist/" ]; then
    echo "build dist directory does't exists. . ."
    rm -f "../dist/*"
else
    echo "build dist directory does't exists. . ."
    mkdir -p "../dist/"
fi

cp -r build/* ../dist && rm -r build
echo "Build completed."
