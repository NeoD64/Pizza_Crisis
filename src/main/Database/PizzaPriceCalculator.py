
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