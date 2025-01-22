import re
import json
import pandas as pd
from PIL import Image
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai


google_api_key = st.secrets["GOOGLE_API_KEY"]


def get_gemini_response(input_prompt, image):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([input_prompt, image[0]])
    return response.text

def input_image_setup(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        image_parts = [
            {
                "mime_type": uploaded_file.type,
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded")

def create_dietary_component_graph(data):
    if "Dietary Components" in data:
        components = data["Dietary Components"]
        labels = list(components.keys())
        values = list(components.values())

        fig = px.pie(values=values, names=labels)
        return fig
    return None


def create_environmental_impact_graph(data):
    if "Environmental Impact" in data:
        impact = data["Environmental Impact"]
        labels = list(impact.keys())
        values = list(impact.values())

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.5,  
            textinfo='percent',  
            hoverinfo='label+value',  
            marker=dict(colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])  
        )])

        fig.update_layout(
            showlegend=True,
            template="plotly_white",
            annotations=[dict(
                text='Impact',
                x=0.5,
                y=0.5,
                font_size=16,
                showarrow=False
            )]
        )

        return fig
    return None

st.set_page_config(page_title="Health App")
st.header("Health App")

uploaded_file = st.file_uploader("Choose an image...", type=['png', 'jpg', 'jpeg'])
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded image.", use_container_width=True)

input_prompt = """
You are a nutrition expert. Analyze the food items in the image and provide the following details in the exact JSON format:

{
    "Dietary Components": {
        "Carbohydrates": <percentage>,
        "Fats": <percentage>,
        "Proteins": <percentage>,
        "Fibers": <percentage>,
        "Sugar": <percentage>,
        "Vitamins": <percentage>,
        "Minerals": <percentage>,
        "Others": <percentage>
    },
    "Total Calories": <total_calories>,
    "Health Assessment": "<short assessment of whether the food is healthy or not>",
    "Macro Nutrient Ratio": {
        "Carbs": "<percentage>",
        "Fats": "<percentage>",
        "Proteins": "<percentage>"
    },
    "Micro Nutrient Details": {
        "Vitamin A": "<percentage of daily recommended value>",
        "Vitamin C": "<percentage of daily recommended value>",
        "Calcium": "<percentage of daily recommended value>",
        "Iron": "<percentage of daily recommended value>"
    },
    "Health Recommendations": {
        "Ideal Serving Size": "<recommended serving size>",
        "Recommended For": "<target audience or groups>",
        "Avoid For": "<groups or conditions to avoid>"
    },
    "Allergy Warnings": [
        "<warning 1>",
        "<warning 2>"
    ],
     "Environmental Impact": {
        "Carbon Footprint (kg CO2e per serving)": <numeric_value>,
        "Water Usage (liters per serving)": <numeric_value>,
        "Sustainability Score (out of 10)": <numeric_value>
    }
}

Ensure the percentages of dietary components sum up to 100%. Provide concise but accurate information for all fields.
Note:Don't add '%' symbol in any

"""

submit = st.button("Analyze Food Image")
if submit:
    try:
        image_data = input_image_setup(uploaded_file)
        response = get_gemini_response(input_prompt, image_data)

        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed_data = json.loads(json_str)

                if "Total Calories" in parsed_data:
                    st.subheader(f"Total Calories: {parsed_data['Total Calories']}")

                if "Health Assessment" in parsed_data:
                    st.subheader(f"Health Assessment: {parsed_data['Health Assessment']}")

                if "Dietary Components" in parsed_data:
                    st.subheader("Dietary Components Data")
                    dietary_components = parsed_data["Dietary Components"]
                    df = pd.DataFrame(list(dietary_components.items()), columns=["Component", "Percentage"])
                    df_transposed = df.set_index("Component").T.reset_index(drop=True)
                    
                    st.table(df_transposed)

                fig1 = create_dietary_component_graph(parsed_data)
                if fig1:
                    st.subheader("Dietary Component Distribution")
                    st.plotly_chart(fig1)

                fig_env = create_environmental_impact_graph(parsed_data)
                if fig_env:
                    st.subheader("Environmental Impact Metrics")
                    st.plotly_chart(fig_env)

                st.markdown(
                    """
                    **Disclaimer:**  
                    The information provided by this app is for informational purposes only and is not intended as a substitute for professional 
                    medical, nutritional, or environmental advice. Always consult a qualified healthcare provider or nutritionist for personalized guidance.  
                    """
                )
            else:
                st.error("No JSON found in the response.")

        except json.JSONDecodeError:
            st.error("Failed to parse AI response into JSON. Please check the response format.")

    except Exception as e:
        st.error(f"An error occurred: {e}")




