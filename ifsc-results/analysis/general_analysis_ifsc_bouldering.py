
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set up visualization style
sns.set(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

def load_and_prepare_data(filepaths):
    """Load and prepare the data"""

    df = pd.DataFrame([])
    for path in filepaths:
        df_ = pd.read_csv(path)
        df = pd.concat([df, df_])

    #fix rounds flags
    df.loc[df["round"] == 'Semi-Final', 'round'] = 'Semi-final'

    # Convert attempts to numeric (they might be strings)
    df['top'] = pd.to_numeric(df['top'], errors='coerce')
    df['zone'] = pd.to_numeric(df['zone'], errors='coerce')

    # Create success flags
    df['top_success'] = df['top'].notna()
    df['zone_success'] = df['zone'].notna()

    # Create performance metrics
    df['total_attempts'] = df['top'].fillna(99)  # 99 represents failed attempts
    df['attempts_diff'] = df['top'] - df['zone']

    return df


def general_overview(df):
    """Print general overview of the dataset"""
    print("=== GENERAL OVERVIEW ===")
    print(f"Total records: {len(df)}")
    print(f"Unique athletes: {df['athlete'].nunique()}")
    print(f"Unique countries where the athletes are from: {df['country'].nunique()}")
    print(f"Unique events: {df['event'].nunique()}")
    # print("\nData types and missing values:")
    # print(df.info())

    print("\n=== COMPETITION STRUCTURE ===")
    print("Observations by year:")
    print(df['event'].str.extract(r'(\d{4})')[0].value_counts().sort_index())

    print("\nRounds distribution:")
    print(df['round'].value_counts(normalize=True))

    print("\nDiscipline distribution:")
    print(df['discipline'].value_counts(normalize=True))


def performance_analysis(df):
    """Analyze performance metrics"""
    print("\n=== PERFORMANCE ANALYSIS ===")

    # Success rates
    print("\nSuccess rates:")
    print(f"Top success rate: {df['top_success'].mean():.1%}")
    print(f"Zone success rate: {df['zone_success'].mean():.1%}")

    # Attempts distribution
    print("\nAttempts distribution for successful tops:")
    print(df[df['top_success']]['top'].describe(percentiles=[.1, .25, .5, .75, .9]))

    print("\nAttempts distribution for successful zones:")
    print(df[df['zone_success']]['zone'].describe(percentiles=[.1, .25, .5, .75, .9]))

    # Plot success rates by round and discipline
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x='round', y='top_success', hue='discipline',
                order=['Qualification', 'Semi-final', 'Final'], errorbar=None)
    plt.title('Top Success Rate by Round and Discipline')
    plt.ylabel('Success Rate')
    plt.show(block = True)

    # Plot attempts distribution
    plt.figure(figsize=(12, 6))
    sns.boxplot(data=df[df['top_success']], x='round', y='top', hue='discipline',
                order=['Qualification', 'Semi-final', 'Final'])
    plt.title('Distribution of Attempts Needed for Top (Successful Attempts Only)')
    plt.show(block = True)


def athlete_analysis(df):
    """Analyze athlete performance"""
    print("\n=== ATHLETE ANALYSIS ===")

    # Top athletes by success rate (minimum 20 boulders attempted)
    athlete_stats = df.groupby(['athlete', 'country', 'discipline']).agg(
        boulders_attempted=('top', 'size'),
        top_success_rate=('top_success', 'mean'),
        avg_top_attempts=('top', lambda x: x[x.notna()].mean()),
        avg_zone_attempts=('zone', lambda x: x[x.notna()].mean())
    ).reset_index()

    top_athletes = athlete_stats[athlete_stats['boulders_attempted'] >= 20].sort_values(
        'top_success_rate', ascending=False).head(10)

    print("\nTop 10 athletes by success rate (min 20 boulders):")
    print(top_athletes)

    # Plot athlete performance
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=athlete_stats[athlete_stats['boulders_attempted'] >= 20],
                    x='avg_top_attempts', y='top_success_rate', hue='discipline')
    plt.title('Athlete Performance: Success Rate vs Average Attempts Needed')
    plt.xlabel('Average Attempts Needed for Top (when successful)')
    plt.ylabel('Top Success Rate')
    plt.show(block = True)


def boulder_analysis(df):
    """Analyze boulder difficulty"""
    print("\n=== BOULDER ANALYSIS ===")

    boulder_stats = df.groupby(['event', 'round', 'discipline', 'boulder']).agg(
        attempts=('top', 'size'),
        top_success_rate=('top_success', 'mean'),
        zone_success_rate=('zone_success', 'mean'),
        avg_top_attempts=('top', lambda x: x[x.notna()].mean()),
        avg_zone_attempts=('zone', lambda x: x[x.notna()].mean())
    ).reset_index()

    # Hardest boulders (lowest success rate, minimum 20 attempts)
    hardest_boulders = boulder_stats[boulder_stats['attempts'] >= 20].sort_values(
        'top_success_rate').head(10)

    print("\nTop 10 hardest boulders (lowest success rate):")
    print(hardest_boulders[['event', 'round', 'discipline', 'boulder', 'attempts', 'top_success_rate']])

    # Plot boulder difficulty progression through rounds
    plt.figure(figsize=(12, 6))
    sns.boxplot(data=boulder_stats, x='round', y='top_success_rate', hue='discipline',
                order=['Qualification', 'Semi-final', 'Final'])
    plt.title('Boulder Difficulty by Round')
    plt.ylabel('Top Success Rate')
    plt.show(block = True)


def country_analysis(df):
    """Analyze country performance with enhanced visualizations"""
    print("\n=== COUNTRY ANALYSIS ===")

    # Calculate country statistics
    country_stats = df.groupby(['country', 'discipline']).agg(
        athletes=('athlete', 'nunique'),
        boulders_attempted=('top', 'size'),
        boulders_zoned=('zone_success', 'sum'),
        boulders_topped=('top_success', 'sum'),
        top_success_rate=('top_success', 'mean'),
        zone_success_rate=('zone_success', 'mean'),
        avg_top_attempts=('top', lambda x: x[x.notna()].mean()),
        avg_zone_attempts=('zone', lambda x: x[x.notna()].mean())
    ).reset_index()

    # Filter countries with at least 50 boulders attempted
    country_stats = country_stats[country_stats['boulders_attempted'] >= 50]

    print("\nCountry performance (min 50 boulders attempted):")
    print(country_stats.sort_values('top_success_rate', ascending=False))

    # 1. Performance scatter plot
    plt.figure(figsize=(14, 8))
    sns.scatterplot(data=country_stats, x='avg_top_attempts', y='top_success_rate',
                    hue='discipline', size='athletes', sizes=(50, 300))
    plt.title('Country Performance: Success Rate vs Average Attempts Needed')
    plt.xlabel('Average Attempts Needed for Top (when successful)')
    plt.ylabel('Top Success Rate')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show(block = True)

    # 2. NEW: Stacked bar plot of boulders attempted, zoned, and topped
    # Prepare data for plotting
    plot_data = country_stats.sort_values('boulders_attempted', ascending=False).head(15)
    plot_data['boulders_failed_zone'] = plot_data['boulders_attempted'] - plot_data['boulders_zoned']
    plot_data['boulders_zoned_only'] = plot_data['boulders_zoned'] - plot_data['boulders_topped']

    # Create stacked bar plot
    plt.figure(figsize=(16, 8))

    # Create bars for each segment
    bars1 = plt.barh(plot_data['country'] + " (" + plot_data['discipline'] + ")",
                     plot_data['boulders_topped'], color='#2ecc71', label='Topped')
    bars2 = plt.barh(plot_data['country'] + " (" + plot_data['discipline'] + ")",
                     plot_data['boulders_zoned_only'], left=plot_data['boulders_topped'],
                     color='#f39c12', label='Zoned Only')
    bars3 = plt.barh(plot_data['country'] + " (" + plot_data['discipline'] + ")",
                     plot_data['boulders_failed_zone'],
                     left=plot_data['boulders_topped'] + plot_data['boulders_zoned_only'],
                     color='#e74c3c', label='Failed Zone')

    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            width = bar.get_width()
            if width > 0:
                plt.text(bar.get_x() + width / 2, bar.get_y() + bar.get_height() / 2,
                         f'{int(width)}', ha='center', va='center', color='white', fontsize=8)

    plt.xlabel('Number of Boulders')
    plt.title('Boulder Performance by Country: Attempted, Zoned, and Topped (Top 15 by Attempts)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show(block = True)

    # 3. Success rate comparison by country
    plt.figure(figsize=(14, 8))
    plot_data = country_stats.sort_values('top_success_rate', ascending=False).head(15)
    plot_data_melted = plot_data.melt(id_vars=['country', 'discipline'],
                                      value_vars=['top_success_rate', 'zone_success_rate'],
                                      var_name='metric', value_name='rate')
    plot_data_melted['metric'] = plot_data_melted['metric'].replace({
        'top_success_rate': 'Top Success',
        'zone_success_rate': 'Zone Success'
    })

    sns.barplot(data=plot_data_melted, x='rate', y='country', hue='metric',
                palette=['#2ecc71', '#f39c12'])
    plt.title('Top 15 Countries by Top Success Rate (Comparison with Zone Success)')
    plt.xlabel('Success Rate')
    plt.ylabel('Country')
    plt.xlim(0, 1)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show(block = True)


def temporal_analysis(df):
    """Analyze performance trends over time"""
    print("\n=== TEMPORAL ANALYSIS ===")

    # Extract year from event name
    df['year'] = df['event'].str.extract(r'(\d{4})')[0]

    if pd.api.types.is_numeric_dtype(df['year']):
        yearly_stats = df.groupby(['year', 'discipline']).agg(
            top_success_rate=('top_success', 'mean'),
            avg_top_attempts=('top', lambda x: x[x.notna()].mean())
        ).reset_index()

        print("\nPerformance trends by year:")
        print(yearly_stats.pivot(index='year', columns='discipline',
                                 values=['top_success_rate', 'avg_top_attempts']))

        # Plot trends
        plt.figure(figsize=(14, 6))
        sns.lineplot(data=yearly_stats, x='year', y='top_success_rate', hue='discipline')
        plt.title('Top Success Rate Over Time')
        plt.show()
    else:
        print("Could not extract year from event names for temporal analysis")


def main():
    # Load your data - replace with your actual file path
    filepaths = ['C:\\Data\\climbing\\bouldering_Worldcups_2015_to_2019.csv',
                 'C:\\Data\\climbing\\bouldering_Worldcups_2021_to_2024.csv']
    df = load_and_prepare_data(filepaths)

    # Run analyses
    general_overview(df)
    performance_analysis(df)
    athlete_analysis(df)
    boulder_analysis(df)
    country_analysis(df)
    temporal_analysis(df)


if __name__ == "__main__":
    main()