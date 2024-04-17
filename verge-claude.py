import os
import anthropic

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key="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",
)

def summarize_article(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        article_content = file.read()

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=4000,
        system = ('You are an article summarizer. A headless browser will scrape the contents of an article, and your role is to turn it into a succinct, bullet point based read. It is from the verge. They include extra content, unrelated to the article, which should be ignored. The end of the article is marked by the content "NEW FEATURED VIDEOS FROM THE VERGE" - disregard everything after that, that text showing up signifies the end of the article and the end of the content you should consider. Make sure your summary is strictly a summary of the article, never include additional information - always just return the article. So if you have additional information, eg you know when something in an article was implemented, or you know more about something briefly mentioned, do not include that in your return. Just focus on the content supplied to you. Your summary should 1) Start with the title 2) Have a very brief intro explaining what the article is about 3) Have 2-6 bullet points explaining what is covered in the article. For smaller articles, use less bullet points, only use more if there truly are lots of things to discuss. If a person is quoted, and the quote is relevant, include the full quote in the return and attribute it to who it is attributed to in the article. 4) Close with A very brief outro summarizing the article 5) Finally include the URL of the article'),
        temperature=0,
        messages=[{"role": "user", "content": article_content}]
    )

    summary_file_path = file_path.replace('article', 'summary')
    with open(summary_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(str(response.content))

# Process each article file
for file_name in os.listdir():
    if file_name.startswith("verge-article-") and file_name.endswith(".txt"):
        summarize_article(file_name)