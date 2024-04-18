require("dotenv").config();
const { createClient } = require("@supabase/supabase-js");
const puppeteer = require("puppeteer");

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

async function scrapeArticles() {
  const { data: urls, error } = await supabase
    .from("rss_urls")
    .select("id, url")
    .eq("scraped", false); // Fetch URLs that haven't been scraped yet

  if (error) {
    console.error("Error fetching URLs:", error);
    return;
  }

  const browser = await puppeteer.launch();
  for (const { id, url } of urls) {
    try {
      const page = await browser.newPage();
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 }); // Increased timeout and changed waitUntil
      const content = await page.evaluate(
        () => document.body.innerText || "No content found"
      );

      // Update the table with the scraped content
      const { error: updateError } = await supabase
        .from("rss_urls")
        .update({ content: content, scraped: true })
        .eq("id", id);

      if (updateError) {
        console.error(`Failed to update content for URL ${url}:`, updateError);
      }

      await page.close();
    } catch (e) {
      console.error(`Error processing URL ${url}:`, e.message);
      // Optionally handle the error more specifically, log to a service, or retry logic
    }
  }
  await browser.close();
}

scrapeArticles();
