import openai
from dotenv import load_dotenv
import os
import json
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

SYSTEM_MESSAGE = """
You are an Overwatch hero historian and data analyst. You will be provided with JSON data containing information about a specific Overwatch hero's abilities and their changelog history over several patches. Your task is to analyze this data and generate a historical assessment of the hero's changes, including their name, ability-specific change scores, and an overall judgment. The output should be in JSON format and include historical data for multiple patches.

Here's a template for your response:
{
    "hero_name": "Hero Name",
    "hero_assessment": "Your assessment of the hero's changes.",
    "historical_changes": [
        {
            "patch_date": "Patch Date",
            "ability_changes_judgements": {
                "Ability Name": [
                    {
                        "score": X,
                        "changes": [
                            "Change description (Score)"
                        ]
                    }
                ]
            },
            "overall_judgement": "Overall judgment of the hero's state."
        },
        {
            "patch_date": "Patch Date",
            ...
        },
        ...
    ]
}
"""

INITIAL_PROMPT = """
Please provide the JSON data for the Overwatch hero you want to analyze, including their abilities and changelog history. Once I have the data, I will proceed with the analysis and generate a historical assessment of the hero's changes.
"""

USER_PROMPT = """
I'd like you to analyze the JSON data I'm providing, which contains information about an Overwatch hero and their ability changes over several patches. Please evaluate these changes and generate a historical assessment in JSON format.

The JSON data includes details about the hero's abilities, their stats, and a changelog with information about when and how the abilities were changed in different patches. Assess each patch's impact on their abilities and overall performance, and provide an overall judgment of the hero's state.
When providing judging the sentiment of a change, take into consideration the following:
 - Cooldown reduction is postive. Cooldown increase is negative
 - Increased health/armor/shields is positive. Changing health to armor/shields is positive. Changing armor/shields to health is negative.
 - Increased damage is positive. Reduced damage is negative
 - Redcued delays are positive. Reduced delays are negative
 - Increased effect durations are positive. Reduced effect durations are negative. 
 - Not dealing damage to self is positive
 - Increased ultimate cost is negative. Reduced ultimate cost is positive
If a change is reverted in a later patch, its score should be the inverse of the original change (for eg: 1 and -1)

The "hero_assessment" should contain information on the number of positive and negative changes made to the hero. It should have commentary on what direction the changes have pushed the hero and a detailed analysis on the current state of the hero
Your assessment should include a score out of 10 for the current state of the hero, considering the positive and negative changes made to it.
Once you have completed the analysis, present the data in the format specified in the system prompt.
"""
if __name__ == "__main__":
    for json_file in os.listdir('./heroes'):
        print(json_file)
        with open(os.path.join('./heroes', json_file), 'r') as fn:
            hero_data = json.load(fn)
            
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0301", 
            messages=[
                {"role": "system", "content":SYSTEM_MESSAGE},
                {"role": "user", "content": USER_PROMPT},
                {"role": "assistant", "content": INITIAL_PROMPT},
                {"role": "user", "content": json.dumps(hero_data)},
            ],
            temperature=0.4
        )
        output = completion.choices[0].message.content
        
        if not os.path.exists('./judgements'):
            os.mkdir('./judgements')
            
        try:
            output = output.replace('\n', '')
            output_obj = json.loads(output)
            with open(os.path.join('./judgements', json_file), 'w+') as fn:
                json.dump(output_obj, fn, indent=4)
        except:
            print(f'{json_file} - output wasnt valid json...')
            hero_name = json_file.rstrip('.json')
            with open(os.path.join('./judgements', f"{hero_name}.txt"), 'w+') as fn:
                fn.writelines(output)