"""
Prompt generation functions for the World Model Actor system.

This module contains all the prompt templates and generation logic for:
- Initial actor generation (Level 0)
- Level-specific sub-actor generation (Levels 1-4+)
"""

from typing import Tuple


def generate_initial_actor_prompts(num_actors: int) -> Tuple[str, str]:
    """
    Generate system and user prompts for initial actor generation (Level 0).
    
    Args:
        num_actors (int): Number of actors to generate
        
    Returns:
        Tuple[str, str]: (system_context, user_context)
    """
    
    system_context = (
        "You are an expert in geopolitics, international relations, and global power dynamics. "
        "Your task is to identify and rank the most influential actors that shape our world today. "
        "These actors should be the ones with the greatest impact on global economics, politics, "
        "technology, culture, and society. Focus on entities that have the power to influence "
        "international relations, global markets, and major world events.\n\n"
        
        "Return ONLY a valid JSON object with the following structure:\n"
        "{\n"
        '  "actors": [\n'
        '    {\n'
        '      "name": "Actor Name",\n'
        '      "description": "Brief description of their influence and role",\n'
        '      "type": "country|company|organization|individual|alliance"\n'
        '    }\n'
        '  ],\n'
        '  "total_count": number_of_actors\n'
        "}\n\n"
        "Do not include any explanation or text outside the JSON.\n\n"
    )

    user_context = (
        f"Generate a list of the {num_actors} most influential actors in the world today. "
        "These should be the entities that have the greatest power to shape global dynamics. "
        "Consider the following categories and prioritize the most impactful:\n\n"
        
        "**Countries**: Major world powers, economic superpowers, regional hegemons\n"
        "**Companies**: Multinational corporations, tech giants, financial institutions, energy companies\n"
        "**Organizations**: International bodies (UN, IMF, WTO), military alliances (NATO), economic blocs (EU, G7, G20)\n"
        "**Individuals**: World leaders, tech moguls, financial leaders, influential figures\n"
        "**Alliances**: Political, economic, or military partnerships\n\n"
        
        "For each actor, provide:\n"
        "- **name**: The official name of the actor\n"
        "- **description**: A concise explanation of their influence and global impact\n"
        "- **type**: One of: country, company, organization, individual, alliance\n"
        
        "Rank them by influence score (highest first). Consider factors like:\n"
        "- Economic power and market capitalization\n"
        "- Political influence and diplomatic reach\n"
        "- Military capabilities and strategic importance\n"
        "- Technological innovation and control\n"
        "- Cultural and social influence\n"
        "- Resource control and energy influence\n"
        "- Population and demographic impact\n\n"
        
        f"Return exactly {num_actors} actors in the JSON format specified above."
    )
    
    return system_context, user_context


def generate_leveldown_prompts(actor_name: str, actor_description: str, actor_type: str, 
                              num_subactors: int, current_level: int) -> Tuple[str, str]:
    """
    Generate level-specific system and user prompts for sub-actor generation.
    
    Args:
        actor_name (str): Name of the parent actor
        actor_description (str): Description of the parent actor
        actor_type (str): Type of the parent actor
        num_subactors (int): Number of sub-actors to generate
        current_level (int): Current level being generated (1=countries, 2=companies, 3=people, 4=movements)
        
    Returns:
        Tuple[str, str]: (system_context, user_context)
    """
    
    if current_level == 1:
        # Level 1: Countries/Nations focus
        system_context = (
            "You are an expert in geopolitics and international relations specializing in national governance structures. "
            "Your task is to identify the most influential governmental, institutional, and organizational sub-entities "
            "within a given country or nation-state. Focus on the key power centers that shape national policy and influence.\n\n"
            
            "Return ONLY a valid JSON object with the following structure:\n"
            "{\n"
            '  "sub_actors": [\n'
            '    {\n'
            '      "name": "Sub-Actor Name",\n'
            '      "description": "Detailed description of their governmental role and national influence",\n'
            '      "type": "government|ministry|agency|party|military|institution|other",\n'
            '      "parent_actor": "' + actor_name + '"\n'
            '    }\n'
            '  ],\n'
            '  "total_count": number_of_sub_actors,\n'
            '  "parent_actor": "' + actor_name + '"\n'
            "}\n\n"
            "Do not include any explanation or text outside the JSON.\n\n"
        )
        
        user_context = (
            f"Analyze the following country/nation and generate {num_subactors} most influential governmental and institutional sub-actors:\n\n"
            f"**Country/Nation**: {actor_name}\n"
            f"**Type**: {actor_type}\n"
            f"**Description**: {actor_description}\n\n"
            
            f"Generate the {num_subactors} most influential governmental and institutional sub-actors within this nation. "
            f"Focus on: government branches, key ministries, military divisions, intelligence agencies, major political parties, "
            f"central banks, supreme courts, regulatory bodies, and other key national institutions.\n\n"
            
            "For each sub-actor, provide:\n"
            "- **name**: The official name of the governmental/institutional entity\n"
            "- **description**: Their specific role in national governance and policy influence\n"
            "- **type**: Category (government, ministry, agency, party, military, institution, etc.)\n"
            
            "Rank by influence score (highest first). Focus on entities that directly shape national policy, "
            "governance, and strategic decisions.\n\n"
            
            f"Return exactly {num_subactors} sub-actors in the JSON format specified above."
        )
    
    elif current_level == 2:
        # Level 2: Companies/Corporations focus
        system_context = (
            "You are an expert in corporate analysis and business strategy specializing in organizational hierarchies "
            "and corporate power structures. Your task is to identify the most influential companies, corporations, "
            "and business entities that operate within or significantly influence a given parent entity.\n\n"
            
            "Return ONLY a valid JSON object with the following structure:\n"
            "{\n"
            '  "sub_actors": [\n'
            '    {\n'
            '      "name": "Company/Corporation Name",\n'
            '      "description": "Detailed description of their business role and market influence",\n'
            '      "type": "corporation|company|enterprise|conglomerate|startup|subsidiary|other",\n'
            '      "parent_actor": "' + actor_name + '"\n'
            '    }\n'
            '  ],\n'
            '  "total_count": number_of_sub_actors,\n'
            '  "parent_actor": "' + actor_name + '"\n'
            "}\n\n"
            "Do not include any explanation or text outside the JSON.\n\n"
        )
        
        user_context = (
            f"Analyze the following entity and generate {num_subactors} most influential companies and corporations associated with it:\n\n"
            f"**Parent Entity**: {actor_name}\n"
            f"**Type**: {actor_type}\n"
            f"**Description**: {actor_description}\n\n"
            
            f"Generate the {num_subactors} most influential companies and corporations that either operate within, "
            f"are based in, or significantly influence this parent entity. Focus on: major corporations, "
            f"multinational companies, key industry leaders, influential startups, state-owned enterprises, "
            f"conglomerates, and major business groups.\n\n"
            
            "For each sub-actor, provide:\n"
            "- **name**: The official company/corporation name\n"
            "- **description**: Their business focus, market position, and influence within the parent entity\n"
            "- **type**: Category (corporation, company, enterprise, conglomerate, startup, subsidiary, etc.)\n"
            
            "Rank by influence score (highest first). Focus on entities that drive economic activity, "
            "innovation, employment, and strategic business influence.\n\n"
            
            f"Return exactly {num_subactors} sub-actors in the JSON format specified above."
        )
    
    elif current_level == 3:
        # Level 3: Famous People/Individuals focus
        system_context = (
            "You are an expert in influence networks and celebrity analysis specializing in identifying the most "
            "influential individuals, leaders, and public figures. Your task is to identify the most impactful "
            "people who significantly influence, lead, or represent a given parent entity.\n\n"
            
            "Return ONLY a valid JSON object with the following structure:\n"
            "{\n"
            '  "sub_actors": [\n'
            '    {\n'
            '      "name": "Individual Name",\n'
            '      "description": "Detailed description of their role, achievements, and influence",\n'
            '      "type": "ceo|leader|celebrity|politician|expert|influencer|founder|other",\n'
            '      "parent_actor": "' + actor_name + '"\n'
            '    }\n'
            '  ],\n'
            '  "total_count": number_of_sub_actors,\n'
            '  "parent_actor": "' + actor_name + '"\n'
            "}\n\n"
            "Do not include any explanation or text outside the JSON.\n\n"
        )
        
        user_context = (
            f"Analyze the following entity and generate {num_subactors} most influential individuals and famous people associated with it:\n\n"
            f"**Parent Entity**: {actor_name}\n"
            f"**Type**: {actor_type}\n"
            f"**Description**: {actor_description}\n\n"
            
            f"Generate the {num_subactors} most influential individuals who lead, represent, or significantly "
            f"influence this parent entity. Focus on: CEOs and executives, political leaders, celebrities, "
            f"founders and entrepreneurs, thought leaders, experts and academics, public figures, and other "
            f"influential personalities.\n\n"
            
            "For each sub-actor, provide:\n"
            "- **name**: The individual's full name (real person)\n"
            "- **description**: Their role, achievements, and specific influence within/on the parent entity\n"
            "- **type**: Category (ceo, leader, celebrity, politician, expert, influencer, founder, etc.)\n"
            
            "Rank by influence score (highest first). Focus on individuals who shape decisions, "
            "represent the entity publicly, or have significant impact on its direction.\n\n"
            
            f"Return exactly {num_subactors} sub-actors in the JSON format specified above."
        )
    
    elif current_level == 4:
        # Level 4: Social movements, trends, and influencers focus
        system_context = (
            "You are an expert in social dynamics, cultural trends, and grassroots movements specializing in "
            "identifying emerging social phenomena, movements, and cultural influencers. Your task is to identify "
            "the most influential social movements, trends, and cultural phenomena associated with a given parent entity.\n\n"
            
            "Return ONLY a valid JSON object with the following structure:\n"
            "{\n"
            '  "sub_actors": [\n'
            '    {\n'
            '      "name": "Movement/Trend/Phenomenon Name",\n'
            '      "description": "Detailed description of the social/cultural phenomenon and its influence",\n'
            '      "type": "movement|trend|phenomenon|campaign|community|culture|activism|other",\n'
            '      "parent_actor": "' + actor_name + '"\n'
            '    }\n'
            '  ],\n'
            '  "total_count": number_of_sub_actors,\n'
            '  "parent_actor": "' + actor_name + '"\n'
            "}\n\n"
            "Do not include any explanation or text outside the JSON.\n\n"
        )
        
        user_context = (
            f"Analyze the following entity and generate {num_subactors} most influential social movements, trends, and cultural phenomena associated with it:\n\n"
            f"**Parent Entity**: {actor_name}\n"
            f"**Type**: {actor_type}\n"
            f"**Description**: {actor_description}\n\n"
            
            f"Generate the {num_subactors} most influential social movements, cultural trends, and grassroots "
            f"phenomena that either originate from, are supported by, or significantly influence this parent entity. "
            f"Focus on: social movements, cultural trends, activist campaigns, online communities, "
            f"grassroots initiatives, cultural phenomena, and influential social dynamics.\n\n"
            
            "For each sub-actor, provide:\n"
            "- **name**: The name of the movement, trend, or phenomenon\n"
            "- **description**: Their social/cultural impact and influence within/on the parent entity\n"
            "- **type**: Category (movement, trend, phenomenon, campaign, community, culture, activism, etc.)\n"
            
            "Rank by influence score (highest first). Focus on phenomena that shape public opinion, "
            "cultural direction, and social change within the parent entity's sphere.\n\n"
            
            f"Return exactly {num_subactors} sub-actors in the JSON format specified above."
        )
    
    else:
        # Default fallback for levels > 4
        system_context = (
            "You are an expert analyst specializing in organizational structures, hierarchies, and influence networks. "
            "Your task is to identify and analyze the most influential sub-entities within a given main actor. "
            "These sub-actors should be the key components that collectively make up the main actor's influence and power.\n\n"
            
            "Return ONLY a valid JSON object with the following structure:\n"
            "{\n"
            '  "sub_actors": [\n'
            '    {\n'
            '      "name": "Sub-Actor Name",\n'
            '      "description": "Detailed description of their role and influence within the parent actor",\n'
            '      "type": "administration|company|movement|individual|department|institution|faction|other",\n'
            '      "parent_actor": "' + actor_name + '"\n'
            '    }\n'
            '  ],\n'
            '  "total_count": number_of_sub_actors,\n'
            '  "parent_actor": "' + actor_name + '"\n'
            "}\n\n"
            "Do not include any explanation or text outside the JSON.\n\n"
        )
        
        user_context = (
            f"Analyze the following main actor and generate {num_subactors} most influential sub-actors within it:\n\n"
            f"**Main Actor**: {actor_name}\n"
            f"**Type**: {actor_type}\n"
            f"**Description**: {actor_description}\n\n"
            
            f"Generate the {num_subactors} most influential sub-actors that make up or significantly influence this main actor. "
            f"Consider the most relevant sub-entities based on the parent actor's nature and context.\n\n"
            
            "For each sub-actor, provide:\n"
            "- **name**: The specific name of the sub-actor\n"
            "- **description**: A detailed explanation of their role, influence, and importance within the parent actor\n"
            "- **type**: The category of sub-actor (be specific based on context)\n"
            
            "Rank them by influence score within the parent actor's context (highest first). "
            "Focus on the most powerful and influential components that shape the main actor's behavior and decisions.\n\n"
            
            f"Return exactly {num_subactors} sub-actors in the JSON format specified above."
        )
    
    return system_context, user_context 