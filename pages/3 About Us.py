# <---Libraries--->
import streamlit as st
from datetime import date

# <---Streamlit App Configuration-->
st.set_page_config(layout = "wide",
                   page_title = "About Us",)

column_about_us, column_logo = st.columns([3, 1], vertical_alignment = "center")
with column_about_us:
    st.title("About Us")
    st.markdown("We provide useful tools that leverage AI and data to fulfil your informational needs on supply chains.")
    st.caption(f"Last updated: {date.today().strftime('%d %b %Y')}")
with column_logo:
    st.image("assets/logo.png", use_container_width = True)

st.divider()

st.subheader("Problem Statement (Problem)")
st.markdown("""Global supply chains are deeply interconnected and unexpected events, such as political unrest, natural disasters, or sudden regulatory shifts can have rippling effects throughout supply chains.

To address these risks, the MTI Supply Chain and Economic Resilience (SCERD) team, as the Whole-of-Government (WOG) lead, identifies critical gaps and works with agencies and MTI Trade divisions to develop solutions. However, Trade divisions, who often broker the partnerships may lack timely access to updated policy priorities and supply chain resilience market intelligence. There is a risk that Trade divisions might miss opportunities that could address our critical supply chain vulnerabilities.
""")

st.subheader("Key Question / Objective:")
st.info("""How can we ensure that Trade divisions are consistently and efficiently equipped with timely policy and market intelligence to help them identify and pursue partnerships that address Singapore’s supply chain resilience needs?
""")

st.subheader("Problem Statement (Urgency and Severity)")
st.markdown("""
❓**What is wrong with the current situation, how are key stakeholders affected?**
Currently, **policy (SCERD) and Trade officers** must monitor international developments through fragmented, individual news alerts. These alerts are keyword-based, often duplicative, and lack context (i.e., key disruption signals or opportunities may be missed if the exact keyword was not used). This makes it harder for officers to be updated of resilience-relevant insights.

**SCERD and Trade officers** spend significant time manually juxtaposing policy priorities with evolving market intelligence. This often requires repeated alignment to bridge gaps between the **SCERD** (who knows the supply chain resilience gaps) and **Trade divisions** (who broker partnerships). 

As a result, the process of scoping whether a proposed partnership advances Singapore’s supply chain resilience is slow and resource intensive. Trade divisions struggle to quickly assess whether partnership proposals are relevant to supply chain resilience, while SCERD spends additional time clarifying Singapore’s supply chain resilience priorities instead of focusing on strategic planning.

❓**What is the magnitude of this problem?**
1.	Monitoring and synthesizing relevant news: On average, an officer spends 1 to 2 hours per day scanning multiple news sources and reconciling scattered alerts. Across 100 officers in these roles, this amounts to 20,000 to 40,000 productivity hours annually (based on 5 workdays per week, 48 working weeks per year)
2.	Alignment: Officers spend substantial time brainstorming and aligning priorities and partnership opportunities. Using an estimate of 2 to 3 hours/ week/ officer equates to 10,000 to 15,000 hours annually across 100 officers.

3.	Financial Cost: At an estimated manpower cost of $25/hour, the wasted effort across both monitoring and alignment is equivalent to $750,000 to $1.375 mil annually.

4.	Opportunity cost and risk: Beyond manpower and time wasted, Singapore risks missing timely partnership opportunities that could close resilience gaps, or pursuing engagements that do not meaningfully strengthen supply chain resilience.

""")

st.divider()

st.subheader("Solution")
st.markdown("""
We propose building a Supply Chain Resilience AI Assistant comprising an (1) AI-assisted Automated Market Pulsing tool and (2) AI-assisted Chatbox that bridges the gap between policy and trade, by integrating internal policy priorities with market intelligence and external disruption signals. 

1.	Automated “Market Pulsing” email summarises the most relevant and updated developments for users by understanding context of users’ keywords.

2.	AI-assisted Chatbox is based on a repository of policy information/ parameters (which SCERD will internally manage). Trade officers can “upload” market information, including from Automated “Market Pulsing” under “upload” function. AI-assisted Chatbox juxtaposes both information and helps to scope and surface potential collaboration opportunities

The platform reduces manual effort, ensures consistent alignment with Singapore’s supply chain resilience interests and empowers officers to pursue timely and relevant international partnerships.

How the solution addresses the problem: 

1.	Improves horizon scanning: Allows Users to enter engagements with quick and updated insights.

2.	Enhances decision-making: Helps to scope and surface potential collaboration opportunities quickly.

3.	Enhances consistency: Reduces reliance on repeated communications, ensuring Trade and policy offers present a unified, resilience-focused narrative to partners.

4.	Cuts wasted time: Assuming this AI solution can cut the time required in half, it can help to save up to 27,500 productivity hours 


5.	Financial savings: The potential savings are up to $687,500 per year
""")

st.divider()

st.subheader("Scope")
st.write("(includes key stakeholders, functions, key features, how LLMs are involved)")
st.markdown("""
**Key stakeholders**

1.	MTI-SCERD (policy officers)

2.	MTI-Trade divisions

Each officer will have a personal account with role-based access (i.e., admin versus user). Policy officers would be admin officers with access to the policy data repository. 

**Data Sources**

1.	**[Automated Market Pulsing] Market pulsing email summary** function: Connected to Google RSS for latest news 

2.	**[Chatbox]** As a **base repository** for the Chatbox function, maintained by SCERD

    - Singapore’s critical supplies

    - Policy positions on resilience priorities (i.e., diversification, etc.) and vulnerabilities

    - Trade data comprising our dependencies and trade flows to identify vulnerabilities

3.	**[Chat box] Upload function** on Chatbox allows Trade divisions to upload relevant partner-specific information, such as:

    - Engagement minutes, trip reports or proposals from partners

    - Other market intelligence studies from agencies/ Trade divisions

    - Information/ news obtained from AI-assisted Market Pulsing

**Functions, key features and how Large Language Model (LLM) is involved**

- SCERD officers can upload/ delete documents from base repository that the Chatbox is based on.

- **Multi-user Document management:** 

    a.	**Multiple user login:** Interface can allow for multiple users (e.g. policy and Trade officers).

    b.	**Personal libraries:** Trade officers can upload market intelligence documents using “Upload” function in the Chatbox, where **uploaded documents are private by default. Files will be stored in each user’s private library and remain** to be accessed each time the user logs in.

    c.	**Scoped querying:** Before user enters his/ her query in the Chatbox, users can **select specific previously uploaded documents** to include in the chat query, to ensure that answers are based on the correct sources. 

- **Automated Market Pulsing:** Officer can input sector (e.g. “Agriculture”) and market (e.g. “China”); AI generates email with **top 10 most relevant articles** (using Google RSS), with summary of each article’s relevance to resilience and links.

    - **User inputs**: User can provide his/ her email, and the specific industry (e.g. “Agriculture”) and country of interest.

    - **Contextualised smart query expansion: AI expands the topic into relevant keywords/ entities** (e.g. raw materials, key companies, production processes etc.) and **disruption signals** (e.g. port strikes, export bans, extreme weather, logistics bottlenecks, fuel shortages etc. **Examples of risk terms are included within the code).** AI has **context awareness**, meaning it can **detect related terms and interpret meaning.** 

    - **Source sweep:** Will search Google RSS feeds for news

    - **De-duplication and ranking:** AI helps to prioritise recency and relevance

    - **Email summary:** Auto-generates a single email with titles and links to the top 10 articles, and a short paragraph for each article describing the relevant supply chain disruption within the article, for the user’s quick reference.

- **AI-assisted Chatbox:** Query against (a) curated repository of resilience priorities managed by SCERD and (b) user-selected documents (market information, including information from AI-assisted Market Pulsing) from Trade officers. AI highlights opportunities.

    - **Core knowledge repository:** Chatbox is grounded with a base repository of policy positions/ interests, maintained by supply chain resilience policy officers. **AI ensures responses are anchored in this official knowledge, reducing drift and inconsistency.**

    - **Efficient juxtaposing of policies with market intel** after users have uploaded market intelligence through the “Upload” feature. AI **compares market developments with our resilience priorities to surface partnership angles** that can strengthen Singapore's supply chains:
        
        - **Contextualisation: Beyond keyword matching,** AI can recognise implicit links between content.
        - AI is able to explain why the match matters to Singapore.
        - Summarisation: AI can summarize **multiple sources into a single coherent insight.**

""")