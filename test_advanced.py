import streamlit as st
from typing import List


def generate_recipe(ingredients: List[str], must_use: List[str]) -> str:
    """Mock AI recipe generator.

    This function simulates generating a recipe based on the provided ingredients
    and must‑use (expiring) items. It returns a simple formatted string.
    """
    # Basic validation
    if not ingredients:
        return "Please provide at least one ingredient."

    # Ensure must_use items are part of ingredients
    must_use = [item for item in must_use if item in ingredients]

    # Simple mock logic: list must‑use items first, then other ingredients.
    recipe_ingredients = must_use + [i for i in ingredients if i not in must_use]
    ingredient_list = ", ".join(recipe_ingredients)

    # Mock recipe text
    recipe = (
        f"## Your Custom FridgeChef Recipe\n"
        f"**Ingredients**: {ingredient_list}\n\n"
        "**Instructions**:\n"
        "1. Gather all ingredients.\n"
        "2. Preheat your oven or stovetop as appropriate.\n"
        "3. Combine the ingredients in a bowl and mix well.\n"
        "4. Cook or bake until done.\n"
        "5. Serve hot and enjoy your meal!"
    )
    return recipe


def main() -> None:
    st.set_page_config(page_title="FridgeChef", page_icon="🥦", layout="centered")
    st.title("🥦 FridgeChef – Create Recipes from Your Ingredients")
    st.write(
        "Enter the ingredients you have on hand. "
        "Select any items that are expiring soon (must‑use) to prioritize them in the recipe."
    )

    # Input: free‑form list of ingredients
    ingredients_input = st.text_area(
        "List your ingredients (comma‑separated)",
        placeholder="e.g., chicken, tomatoes, basil, cheese, milk",
        height=100,
    )

    # Parse ingredients
    ingredients = [i.strip() for i in ingredients_input.split(',') if i.strip()]

    if ingredients:
        # Let user pick must‑use items from the parsed list
        must_use = st.multiselect(
            "Select expiring (must‑use) ingredients", options=ingredients
        )
    else:
        must_use = []

    if st.button("Generate Recipe"):
        with st.spinner("Cooking up a recipe…"):
            recipe = generate_recipe(ingredients, must_use)
        st.markdown(recipe)


if __name__ == "__main__":
    main()
