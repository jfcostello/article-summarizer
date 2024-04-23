#!/root/.ssh/article-summarizer/as-env/bin/python3
import os
import json
from datetime import datetime, timezone
from supabase import create_client, Client
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase setup using environment variables
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'), 
    os.getenv('SUPABASE_KEY')
)

# Groqs client setup using environment variable
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# Define script_name globally
script_name = "groq_llama_8b.py"

def log_status(script_name, log_entries, status):
    """Logs script execution status and messages."""
    supabase.table("log_script_status").insert({
        "script_name": script_name,
        "log_entry": json.dumps(log_entries),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status
    }).execute()


def log_duration(script_name, start_time, end_time):
    """Logs script execution duration."""
    duration_seconds = (end_time - start_time).total_seconds()
    supabase.table("log_script_duration").insert({
        "script_name": script_name,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": duration_seconds
    }).execute()

def fetch_articles():
    """Fetch articles that have been scraped but not summarized."""
    response = supabase.table("summarizer_flow").select("id, content").eq("scraped", True).eq("summarized", False).execute()
    articles = response.data if response.data else []
    return articles

def extract_section(content, start_key, end_key=None):
    """Extract text between start_key and optional end_key from content."""
    start_idx = content.find(start_key)
    if start_idx == -1:
        return ""  # start_key not found
    start_idx += len(start_key)
    if end_key:
        end_idx = content.find(end_key, start_idx)
        if end_idx == -1:
            end_idx = len(content)  # end_key not found, take until end
    else:
        end_idx = len(content)  # No end_key provided, take until end
    return content[start_idx:end_idx].strip()

def summarize_article(article_id, content, status_entries):
    try:
        chat_completion = client.chat.completions.create(
            model="llama3-8b-8192",
            max_tokens=4000,
            temperature=0,
            messages=[
                {"role": "user", "content": content},
                {"role": "system", "content": '''You are an pipe-seperated values (PSV) creator, you respond only with a valid PSV using | as your seperator, that is the only response you will ever give. A headless browser will scrape the contents of an article, and your role is to turn it into a succinct bullet point based summary which will be delivered in pipe-separated values. Your response should only be in pipe separated values, as it will be ingested into a database directly, again, | is how you will show a new section. Do not include anything else. When creating the summary, make sure you focus only on the article itself. You will get the full page, but ignore any additional articles, comments etc. The article will be the bulk of the return, usually starting with a title and ending with comments, a heading promoting additional articles, a complete change in tone things of that nature - you should only focus on the article, so look out for signs the article ended, like a conclusion or a sudden change into comments, other articles, footers etc. Focus on only summarizing, do not add additional information or context - if it's not in the article, don't include it. Your summary should 1) Have a very brief intro summarizing the main argument. Focus on the argument, do not use language like 'in this article', instead go straight into an introduction for the arguments presented 2) Have 2-6 bullet points explaining what is covered in the article. For smaller articles, use less bullet points, only use more if there truly are lots of things to discuss. If a person is quoted, and the quote is relevant, include the full quote in the return and attribute it to who it is attributed to in the article. Wrap each individual bullet point in ""s, so we can seperate them, it's imperative we can import each INDIVUDUAL bullet point so each one MUST be wrapped in "", that is how we will know the beginning of each bullet point. So for each individual bullet point put them in "s, start and end each one with " 3) Close with A very brief outro summarizing the article. This will be returned in pipe-separated values as follows —-"IntroParagraph: BRIEF INTRO THAT EXPLAINS THE ARGUMENTS PRESENTED GOES HERE|BulletPointSummary: "BULLET POINT GOES HERE" "ADDITIONAL BULLET POINT GOES HERE" "CONTINUE WITH BULLET POINTS AS NECESSARY, ENDING WITH 2-6 DEPENDING ON HOW MANY DISTINCT TOPICS ARE DISCUSSED IN THE ARTICLE"|ConcludingParagraph: BRIEF CONCLUDING PARAGRAPH GOES HERE, WRAPPING UP THE ARGUMENTS PRESENTED". Rememeber, return everything in one line, do not use line breaks instead everything must be sepetrated using | that is how we will know the beginning of each new section so it is absolutely imperative they are seperated using | or it will not be valid output. Remember, do not include any additional content, the first word in your response should be IntroParagraph. Here's two examples of a valid output — IntroParagraph: Fintech startup Fundid was forced to shut down due to rising interest rates and a strained cap table, but its founder Stefanie Sample is already back with a new investment company called Pailor Capital to help women buy and grow existing profitable businesses.|BulletPointSummary: "Fundid was a fintech company that offered lending via a business-building credit card and finance resources like a grant-matching tool, primarily targeting women business owners" "The company had to wind down operations after the Federal Reserve raised interest rates 11 times between spring 2022 and the end of 2023, causing the debt facility partner's costs to skyrocket and making Fundid's business model unsustainable" "Sample was reluctant to raise more capital and dilute her ownership further, as she felt female founders often have to sacrifice more and accept worse term sheets compared to their male counterparts" "After shutting down Fundid, Sample launched a new investment company called Pailor Capital to help women find, buy and grow existing profitable businesses, as she believes this is a better way to drive gender equality and business impact"|ConcludingParagraph: Fundid's shutdown was a bittersweet experience for Sample, but it has inspired her to pursue a new path focused on empowering women to become business owners through acquiring and scaling existing profitable companies, which she believes can have a more direct and meaningful impact than the venture capital-backed startup route. - AND A SECOND EXAMPLE -  IntroParagraph: A new study by Mozilla has found that most dating apps are not following good privacy practices and are collecting more user data than ever before in order to appeal to Gen Z users.|BulletPointSummary: "80% of the apps studied may share or sell users' personal data for advertising purposes" "Apps like Bumble have murky privacy clauses that may allow them to sell user data to advertisers" "The majority of apps, including Hinge, Tinder, OKCupid, Match, Plenty of Fish, BLK, and BlackPeopleMeet, collect precise geolocation data from users, even when the app is not in use" "Dating apps claim they collect significant data to find better matches, but if that data ends up with data brokers, there can be grave consequences, as seen with Grindr last year" "Mozilla researchers are not confident that dating apps will have enough protections for user privacy as they start using more AI-powered features to engage potential daters"|ConcludingParagraph: The report highlights the concerning privacy practices of most dating apps, which are collecting more user data than ever before without adequate protections, raising serious concerns about the exploitation of this sensitive information.'''}
            ]
        )

        # Extract the structured text from the response
        response_content = chat_completion.choices[0].message.content
        ## print("Debug - Response Content:", response_content)  # Debugging output
        intro_paragraph = extract_section(response_content, "IntroParagraph:", "BulletPointSummary:")
        bullet_point_summary = extract_section(response_content, "BulletPointSummary:", "ConcludingParagraph:")
        concluding_paragraph = extract_section(response_content, "ConcludingParagraph:")

        update_data = {
            "IntroParagraph": intro_paragraph,
            "BulletPointSummary": bullet_point_summary,
            "ConcludingParagraph": concluding_paragraph,
            "summarized": True
        }

        update_response, update_error = supabase.table("summarizer_flow").update(update_data).eq("id", article_id).execute()

        if update_error and update_error != ('count', None):
            print(f"Failed to update summary for ID {article_id}: {update_error}")
            status_entries.append({"message": f"Failed to update summary for ID {article_id}", "error": str(update_error)})
        else:
            print(f"Summary updated successfully for ID {article_id}")
            status_entries.append({"message": f"Summary updated successfully for ID {article_id}"})
    except Exception as e:
        print(f"Error during the summarization process for ID {article_id}: {str(e)}")
        status_entries.append({"message": f"Error during summarization for ID {article_id}", "error": str(e)})

def main():
    start_time = datetime.now(timezone.utc)
    articles = fetch_articles()
    status_entries = []
    if articles:
        for article in articles:
            summarize_article(article['id'], article['content'], status_entries)
    else:
        print("No articles to summarize.")
        status_entries.append({"message": "No articles to summarize"})

    end_time = datetime.now(timezone.utc)
    log_duration(script_name, start_time, end_time)
    log_status(script_name, status_entries, "Complete")

if __name__ == "__main__":
    main()