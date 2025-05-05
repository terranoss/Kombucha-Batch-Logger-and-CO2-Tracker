"""
CO2 Calculator for Kombucha Fermentation

This module provides functions to estimate CO2 production during kombucha fermentation
based on sugar content, temperature, fermentation time, and batch volume.

The calculations are based on simplified models that approximate real-world fermentation
behavior. While these estimates are useful for tracking trends and relative changes,
they should not be considered precise measurements for safety-critical decisions.

Key functions:
- calculate_co2_production: Estimates CO2 produced from sugar during fermentation
- estimate_fermentation_completion: Calculates percentage of fermentation completed
- estimate_co2: Estimates CO2 pressure in a sealed container
- predict_co2_timeline: Generates a timeline of predicted CO2 production
- calculate_sugar_needed: Estimates sugar needed for target CO2 production

Author: Deen
Email: deen.htc@gmail.com
"""

def calculate_co2_production(sugar_amount, days, temperature=25, volume=1.0):
    """
    Calculate estimated CO2 production during kombucha fermentation.

    The calculation is based on a simplified model where:
    - Sugar is converted to ethanol and CO2 during fermentation
    - Temperature affects fermentation rate
    - Fermentation rate decreases over time as sugar is consumed

    Args:
        sugar_amount (float): Amount of sugar in grams
        days (int): Number of days of fermentation
        temperature (float, optional): Average temperature in Celsius. Defaults to 25.
        volume (float, optional): Volume of the batch in liters. Defaults to 1.0.

    Returns:
        float: Estimated CO2 production in grams
    """
    # Constants for the model
    # Theoretical maximum CO2 production from sugar (approximately 46% of sugar weight)
    MAX_CO2_RATIO = 0.46

    # Temperature adjustment factor (fermentation is faster at higher temperatures)
    # Base temperature is 25°C
    temp_factor = 1.0 + (temperature - 25) * 0.05  # 5% change per degree C

    # Time-based efficiency factor (diminishing returns over time)
    # This models the decreasing fermentation rate as sugar is consumed
    if days <= 0:
        time_factor = 0
    elif days <= 7:
        time_factor = 0.7 * (days / 7)  # Linear increase up to 70% in first week
    elif days <= 14:
        time_factor = 0.7 + 0.2 * ((days - 7) / 7)  # Up to 90% by end of second week
    elif days <= 28:
        time_factor = 0.9 + 0.1 * ((days - 14) / 14)  # Up to 100% by end of fourth week
    else:
        time_factor = 1.0  # Maximum conversion after 28 days

    # Volume adjustment (larger volumes may have slightly lower efficiency)
    volume_factor = 1.0 - (0.05 * max(0, volume - 2) / 10)  # 5% reduction per 10L above 2L
    volume_factor = max(0.8, volume_factor)  # Minimum 80% efficiency

    # Calculate CO2 production
    co2_produced = sugar_amount * MAX_CO2_RATIO * temp_factor * time_factor * volume_factor

    return co2_produced

def estimate_fermentation_completion(sugar_amount, co2_produced):
    """
    Estimate fermentation completion percentage based on CO2 production.

    Args:
        sugar_amount (float): Initial sugar amount in grams
        co2_produced (float): Estimated CO2 produced in grams

    Returns:
        float: Estimated completion percentage (0-100)
    """
    # Theoretical maximum CO2 production
    max_co2 = sugar_amount * 0.46

    # Calculate completion percentage
    completion = (co2_produced / max_co2) * 100 if max_co2 > 0 else 0

    # Cap at 100%
    return min(100, completion)

def predict_co2_timeline(sugar_amount, temperature=25, volume=1.0, days=28):
    """
    Generate a timeline of predicted CO2 production over a specified number of days.

    Args:
        sugar_amount (float): Amount of sugar in grams
        temperature (float, optional): Average temperature in Celsius. Defaults to 25.
        volume (float, optional): Volume of the batch in liters. Defaults to 1.0.
        days (int, optional): Number of days to predict. Defaults to 28.

    Returns:
        dict: Dictionary with days as keys and CO2 production as values
    """
    timeline = {}

    for day in range(days + 1):
        co2 = calculate_co2_production(sugar_amount, day, temperature, volume)
        timeline[day] = co2

    return timeline

def calculate_sugar_needed(target_co2, days, temperature=25, volume=1.0):
    """
    Calculate the amount of sugar needed to produce a target amount of CO2.

    Args:
        target_co2 (float): Target CO2 production in grams
        days (int): Planned fermentation time in days
        temperature (float, optional): Expected temperature in Celsius. Defaults to 25.
        volume (float, optional): Batch volume in liters. Defaults to 1.0.

    Returns:
        float: Estimated sugar needed in grams
    """
    # Start with an initial guess
    initial_sugar = target_co2 / 0.46

    # Use the CO2 calculation function to refine the estimate
    test_co2 = calculate_co2_production(initial_sugar, days, temperature, volume)

    # Simple adjustment factor
    adjustment = target_co2 / test_co2 if test_co2 > 0 else 1.0

    # Calculate adjusted sugar amount
    sugar_needed = initial_sugar * adjustment

    return sugar_needed

def estimate_co2(sugar_content, temp, time_in_days):
    """
    Estimate CO₂ pressure buildup in a sealed container based on sugar content,
    temperature, and fermentation time.

    This function uses a simplified model to estimate the pressure that would
    build up if the CO₂ produced during fermentation were contained in a sealed vessel.

    Args:
        sugar_content (float): Amount of sugar in grams
        temp (float): Temperature in Celsius
        time_in_days (float): Fermentation time in days

    Returns:
        float: Estimated CO₂ pressure in atmospheres (atm)
    """
    # Input validation
    if sugar_content < 0:
        sugar_content = 0
    if time_in_days < 0:
        time_in_days = 0
    
    # Calculate temperature factor
    # Fermentation is faster at higher temperatures
    # Base temperature is 25°C
    temp_factor = 1.0 + (temp - 25) * 0.05  # 5% change per degree C
    
    # Ensure temperature factor is within reasonable bounds
    temp_factor = max(0.5, min(temp_factor, 2.0))
    
    # Calculate time factor with diminishing returns
    # This models the decreasing fermentation rate as sugar is consumed
    if time_in_days <= 0:
        time_factor = 0
    elif time_in_days <= 7:
        time_factor = 0.7 * (time_in_days / 7)  # Linear increase up to 70% in first week
    elif time_in_days <= 14:
        time_factor = 0.7 + 0.2 * ((time_in_days - 7) / 7)  # Up to 90% by end of second week
    elif time_in_days <= 28:
        time_factor = 0.9 + 0.1 * ((time_in_days - 14) / 14)  # Up to 100% by end of fourth week
    else:
        time_factor = 1.0  # Maximum conversion after 28 days

    # Sugar conversion factor (grams of sugar to pressure in atm)
    # This is a simplified conversion factor for demonstration purposes
    # In reality, this would depend on container volume, headspace, etc.
    SUGAR_TO_PRESSURE_FACTOR = 0.01  # 1g of sugar produces 0.01 atm in a typical bottle

    # Calculate CO₂ pressure
    co2_pressure = sugar_content * temp_factor * time_factor * SUGAR_TO_PRESSURE_FACTOR

    return co2_pressure

# Example usage if run directly
if __name__ == "__main__":
    # Example: 200g sugar, 14 days fermentation at 25°C in a 2L batch
    co2 = calculate_co2_production(200, 14, 25, 2.0)
    print(f"Estimated CO2 production: {co2:.2f}g")

    # Example: Generate a timeline
    timeline = predict_co2_timeline(200, 25, 2.0, 14)
    for day, co2 in timeline.items():
        if day % 2 == 0:  # Print every other day to save space
            print(f"Day {day}: {co2:.2f}g CO2")

    # Example: Estimate CO2 pressure
    print("\nCO2 Pressure Estimates:")
    for days in [3, 7, 14, 21]:
        pressure = estimate_co2(200, 25, days)
        print(f"After {days} days: {pressure:.2f} atm")

    # Example: Effect of temperature on CO2 pressure
    print("\nTemperature Effect on CO2 Pressure (after 7 days):")
    for temp in [20, 22, 25, 28, 30]:
        pressure = estimate_co2(200, temp, 7)
        print(f"At {temp}°C: {pressure:.2f} atm")


