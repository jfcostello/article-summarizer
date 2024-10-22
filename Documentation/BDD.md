# Feedbrief Backend BDD

## Table of contents

- [Overview](#overview)
- [Scenario: Fetching URLs from RSS feeds](#scenario-fetching-urls-from-rss-feeds)
- [Scenario: Scraping content from fetched URLs](#scenario-scraping-content-from-fetched-urls)
- [Scenario: Summarizing scraped content](#scenario-summarizing-scraped-content)
- [Scenario: Tagging summarized articles](#scenario-tagging-summarized-articles)
- [Scenario: Full sweep of the process](#scenario-full-sweep-of-the-process)
- [Scenario: Handling errors](#scenario-handling-errors)
- [Scenario: Deduplicating URLs](#scenario-deduplicating-urls)
- [Scenario: Logging script performance](#scenario-logging-script-performance)
- [Scenario: Logging task performance](#scenario-logging-task-performance)

## Overview

- Every 2 minutes, the system will fetch new URLs from all enabled RSS feeds and store them in the database
- If new URLs are found, the system will scrape the content from each URL, summarize the content, tag the article, and store the results in the database
- Every 30 minutes, the system will perform a full sweep of all tasks (URL fetching, scraping, summarizing, and tagging) even if nothing new is found
- If any script in the task logs a 'success' status, the task should log 'success'
- If there is no 'success' status, but a 'partial' status is recorded, the task should log 'partial'
- If there is no 'success' or 'partial' status, the task should log 'error'
- For each task, there is a list of scripts that are queued to run
- It will run each script in a row until the first 'success' status is logged, at which point it will not run any further scripts for that task
- If a script logs a 'partial' or 'error'status, the task will continue to the next script in the queue

## Scenario: Fetching URLs from RSS feeds

- Given the system is running

- When the 2-minute interval timer triggers

- Then the system will add the fetch urls task to our task queue

- Then the system should fetch new URLs from all enabled RSS feeds pulled from Supabase table rss_feed_list

- And store new, unique URLs in the Supabase database table summarizer_flow

- And log the status and duration of the URL fetching process in log_script_status and log_script_duration Supabase tables


## Scenario: Scraping content from fetched URLs

- Given there are new, unscraped URLs in the database

- Then the scraping process is triggered

- Then the system should scrape the content from each URL

- And store the scraped content in the Supabase database summarizer_flow table

- And mark the URL as scraped in the Supabase database summarizer_flow table

- And log the status and duration of the scraping process in log_script_status and log_script_duration Supabase tables


## Scenario: Summarizing scraped content

- Given there are new scraped articles in the database

- Then the summarization process is triggered

- Then the system should use the configured LLM to summarize each article

- The system should check the bullet point summary to ensure it is proper JSON, and show an error if it is not

- And store the summary (intro paragraph, bullet points, and concluding paragraph) in the Supabase database summarizer_flow table

- And mark the article as summarized in the Supabase database summarizer_flow table

- And log the status and duration of the summarization process in log_script_status and log_script_duration Supabase tables


## Scenario: Tagging summarized articles

- Given there are new summarized articles in the database

- Then the tagging process is triggered

- Then the system should pull a list of acceptable tags from the Supabase database article_tags table

- And use the configured LLM to generate tags and scores for each article, using the list of acceptable tags as context and where scores are numbers between 0 and 100

- And store the tags and scores in the Supabase database article_tags table

- And mark the article as tagged in the Supabase database summarizer_flow table

- And log the status and duration of the tagging process in log_script_status and log_script_duration Supabase tables


## Scenario: Full sweep of the process

- Given the system is running

- When the 30-minute interval timer triggers

- Then the system should perform a full sweep of all tasks (URL fetching, scraping, summarizing, and tagging)

- And log the status and duration of the full sweep in log_script_status and log_script_duration Supabase tables


## Scenario: Handling errors

- Given a script is called to preform a task

- If a 'partial' or 'error' status is logged for any reason

- Then the system should log the error in log_script_status Supabase table

- Then the system should call the next script in the queue for that task

- And continue until all scripts have been called, or a 'success' status is reached

- Once a 'success' status is reached for a script, the task no longer continues down the queue and does not call further scripts for this run
  

## Scenario: Deduplicating URLs

- Given a new URL is fetched from an RSS feed

- When the URL is about to be added to the database

- Then the system should check if the URL already exists

- And only add the URL if it's unique

- And log any duplicate URLs that were skipped in the log_script_duration Supabase tables

- And do not log an error if the URL is a duplicate and no other errors occured
  

## Scenario: Logging script performance

- Given any script in the system has completed its execution

- When the script finishes, whether successful or not

- Then the system should log the script's name, status, and duration in the Supabase database

- And include any error messages if the script encountered issues


## Scenario: Logging task performance

- Given any task in the system has completed its execution

- When the task finishes, whether successful or not

- Then the system should log the task's name, status, and duration in the Supabase database

- And include any error messages if the task encountered issues

- If any script in the task logs a 'success' status, the task should log 'success'

- If there is no 'success' status, but a 'partial' status is recorded, the task should log 'partial'

- If there is no 'success' or 'partial' status, the task should log 'error'

