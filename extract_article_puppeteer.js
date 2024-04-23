require("dotenv").config();
const { createClient } = require("@supabase/supabase-js");
const puppeteer = require("puppeteer");

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

const scriptName = "extract_article_puppeteer.js";

async function logStatus(scriptName, logEntries) {
  const logEntry = logEntries.map((entry) => JSON.stringify(entry)).join(", ");
  try {
    const response = await supabase.from("log_script_status").insert({
      script_name: scriptName,
      log_entry: "[" + logEntry + "]",
      timestamp: new Date().toISOString(),
      status: "Success",
    });
    console.log("Log Status Response:", response);
    if (response.error) {
      console.error("Log Status Error:", response.error);
    }
  } catch (err) {
    console.error("Unexpected Error in logStatus:", err);
  }
}

async function logDuration(scriptName, startTime, endTime) {
  const durationSeconds = (endTime - startTime) / 1000;
  try {
    const response = await supabase.from("log_script_duration").insert({
      script_name: scriptName,
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
      duration_seconds: durationSeconds,
    });
    console.log("Log Duration Response:", response);
    if (response.error) {
      console.error("Log Duration Error:", response.error);
    }
  } catch (err) {
    console.error("Unexpected Error in logDuration:", err);
  }
}

async function scrapeArticles() {
  const startTime = new Date();
  let logEntries = []; // Initialize an array to store log entries
  console.log("Starting the scraping process...");
  const { data: urls, error } = await supabase
    .from("summarizer_flow")
    .select("id, url")
    .eq("scraped", false);

  if (error) {
    console.error("Error fetching URLs:", error);
    logEntries.push({
      message: "Failed to fetch URLs due to an error",
      error: JSON.stringify(error),
      status: "Error",
    });
    await logStatus(scriptName, logEntries);
    await logDuration(scriptName, startTime, new Date());
    return;
  }

  if (urls.length === 0) {
    console.log("No URLs to process.");
    logEntries.push({
      message: "No URLs found to process.",
    });
    await logStatus(scriptName, logEntries);
    await logDuration(scriptName, startTime, new Date());
  } else {
    const browser = await puppeteer.launch({
      headless: true,
      args: ["--no-sandbox", "--disable-setuid-sandbox"],
    });
    for (const { id, url } of urls) {
      try {
        const page = await browser.newPage();
        await page.goto(url, { waitUntil: "domcontentloaded", timeout: 10000 });
        const content = await page.evaluate(
          () => document.body.innerText || "No content found"
        );

        const { error: updateError } = await supabase
          .from("summarizer_flow")
          .update({ content: content, scraped: true })
          .eq("id", id);

        if (updateError) {
          console.error(
            `Failed to update content for URL ${url}:`,
            updateError
          );
          logEntries.push({
            message: `Failed to update content for URL ${url}`,
            error: JSON.stringify(updateError),
            status: "Error",
          });
        } else {
          console.log(`Content updated successfully for URL ${url}`);
          logEntries.push({
            message: `Content updated successfully for URL ${url}`,
            status: "Success",
          });
        }

        await page.close();
      } catch (e) {
        console.error(`Error processing URL ${url}:`, e.message);
        logEntries.push({
          message: `Error processing URL ${url}`,
          error: e.message,
          status: "Error",
        });
        await page.close();
      }
    }
    await browser.close();
    await logStatus(scriptName, logEntries);
    await logDuration(scriptName, startTime, new Date());
  }
  console.log("Scraping process completed.");
}

scrapeArticles();
