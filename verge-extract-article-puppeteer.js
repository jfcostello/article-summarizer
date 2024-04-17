const puppeteer = require("puppeteer");
const fs = require("fs");

async function scrapeArticle(url, index) {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: "networkidle2" });

  const content = await page.evaluate(() => {
    const article = document.querySelector("article");
    return article ? article.innerText : "No article content found";
  });

  console.log(`URL: ${url}\nContent:\n${content}`);

  // Create a unique file for each URL
  const fileName = `verge-article-${index}.txt`;
  fs.writeFile(fileName, `URL: ${url}\nContent:\n${content}\n`, (err) => {
    if (err) {
      console.error("Failed to write to file", err);
    } else {
      console.log("File written:", fileName);
    }
  });

  await browser.close();
}

async function processUrls(file) {
  const urls = fs.readFileSync(file, "utf-8").split("\n").filter(Boolean);
  urls.forEach((url, index) => {
    scrapeArticle(url, index);
  });
}

// Pass the file with URLs as an argument
processUrls("verge-urls.txt");
