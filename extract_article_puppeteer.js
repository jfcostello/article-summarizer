require("dotenv").config();
const { createClient } = require("@supabase/supabase-js");
const puppeteer = require("puppeteer");

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

async function scrapeArticles() {
  const { data: urls, error } = await supabase
    .from("summarizer_flow")
    .select("id, url")
    .eq("scraped", false); // Fetch URLs that haven't been scraped yet

  if (error) {
    console.error("Error fetching URLs:", error);
    return;
  }

  const browser = await puppeteer.launch({
    headless: true, // Ensure Puppeteer runs in headless mode
    args: ["--no-sandbox", "--disable-setuid-sandbox"], // Disable sandbox for compatibility with certain environments
  });

  for (const { id, url } of urls) {
    try {
      const page = await browser.newPage();
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 }); // Increased timeout and waitUntil settings
      const content = await page.evaluate(
        () => document.body.innerText || "No content found"
      );

      // Update the table with the scraped content
      const { error: updateError } = await supabase
        .from("summarizer_flow")
        .update({ content: content, scraped: true })
        .eq("id", id);

      if (updateError) {
        console.error(`Failed to update content for URL ${url}:`, updateError);
      }

      await page.close();
    } catch (e) {
      console.error(`Error processing URL ${url}:`, e.message);
    }
  }
  await browser.close();
}

scrapeArticles();
