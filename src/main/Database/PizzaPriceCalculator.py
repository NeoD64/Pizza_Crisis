from sqlalchemy.orm import Session
from Model import Pizza, PizzaIngredient, Ingredient, db



class PizzaPriceCalculator:
    def __init__(self, ingredient_costs: list[float]):
        # where ingredient_costs is the price of each ingredient added on the pizza
        if not ingredient_costs:
            raise ValueError("Pizza must have at least one ingredient")

        if any(c <= 0 for c in ingredient_costs):
            raise ValueError("Ingredient costs must be > 0.")

        self.ingredient_costs = ingredient_costs

    def base_cost(self) -> float:
        return sum(self.ingredient_costs)

    def with_margin(self) -> float:
        return self.base_cost() * 1.40

    def final_price(self) -> float:
        return round(self.with_margin() * 1.09, 2)

    @staticmethod
    def calculate_pizza_price(pizza_id: int) -> float:
        pizza = db.session.get(Pizza, pizza_id)
        if not pizza:
            raise ValueError(f"Pizza with id={pizza_id} not found")

        ingredient_costs = [ingredient.ingredient_price for ingredient in pizza.ingredients]
        calc = PizzaPriceCalculator(ingredient_costs)
        return calc.final_price()

