rm -rf ./public ./docs &&
hugo && 
echo www.kcode.icu >> ./public/CNAME && 
mv public docs
git add . && git commit -m "shell commit..." && git push origin master