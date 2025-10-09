from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from enum import Enum

from app.db.session import get_db
from app.services.auth import get_current_active_user as get_current_user
from app.models.user import User

router = APIRouter()


class SortOrder(str, Enum):
    """Enum for sort order options"""
    asc = "asc"
    desc = "desc"


class SortField(str, Enum):
    """Enum for sort field options"""
    value = "value"
    label = "label"


def filter_and_sort_options(options: List[Dict[str, Any]], search: Optional[str] = None, 
                           sort_by: Optional[SortField] = None, 
                           sort_order: Optional[SortOrder] = SortOrder.asc) -> List[Dict[str, Any]]:
    """
    Helper function to filter and sort options lists.
    
    Args:
        options: List of option dictionaries with 'value' and 'label' keys
        search: Optional search term to filter options
        sort_by: Optional field to sort by
        sort_order: Optional sort order
        
    Returns:
        Filtered and sorted list of options
    """
    # Apply filtering if search parameter is provided
    if search:
        search = search.lower()
        options = [
            option for option in options
            if search in option["value"].lower() or search in option["label"].lower()
        ]
    
    # Apply sorting if sort_by parameter is provided
    if sort_by:
        reverse = sort_order == SortOrder.desc
        options = sorted(options, key=lambda x: x[sort_by], reverse=reverse)
    
    return options


@router.get("/academic-disciplines")
def get_academic_disciplines(
    search: Optional[str] = Query(None, description="Search term to filter disciplines by label or value"),
    sort_by: Optional[SortField] = Query(None, description="Field to sort by"),
    sort_order: Optional[SortOrder] = Query(SortOrder.asc, description="Sort order (ascending or descending)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of academic disciplines with optional filtering and sorting.
    """
    disciplines = [
        {"value": "computer_science", "label": "Computer Science"},
        {"value": "medicine", "label": "Medicine"},
        {"value": "psychology", "label": "Psychology"},
        {"value": "biology", "label": "Biology"},
        {"value": "chemistry", "label": "Chemistry"},
        {"value": "physics", "label": "Physics"},
        {"value": "mathematics", "label": "Mathematics"},
        {"value": "engineering", "label": "Engineering"},
        {"value": "economics", "label": "Economics"},
        {"value": "business", "label": "Business"},
        {"value": "law", "label": "Law"},
        {"value": "education", "label": "Education"},
        {"value": "sociology", "label": "Sociology"},
        {"value": "anthropology", "label": "Anthropology"},
        {"value": "political_science", "label": "Political Science"},
        {"value": "history", "label": "History"},
        {"value": "philosophy", "label": "Philosophy"},
        {"value": "literature", "label": "Literature"},
        {"value": "linguistics", "label": "Linguistics"},
        {"value": "art", "label": "Art"},
        {"value": "music", "label": "Music"},
        {"value": "theater", "label": "Theater"},
        {"value": "film", "label": "Film"},
        {"value": "architecture", "label": "Architecture"},
        {"value": "agriculture", "label": "Agriculture"},
        {"value": "environmental_science", "label": "Environmental Science"},
        {"value": "geography", "label": "Geography"},
        {"value": "geology", "label": "Geology"},
        {"value": "astronomy", "label": "Astronomy"},
        {"value": "other", "label": "Other"}
    ]
    
    return filter_and_sort_options(disciplines, search, sort_by, sort_order)


@router.get("/academic-levels")
def get_academic_levels(
    search: Optional[str] = Query(None, description="Search term to filter levels by label or value"),
    sort_by: Optional[SortField] = Query(None, description="Field to sort by"),
    sort_order: Optional[SortOrder] = Query(SortOrder.asc, description="Sort order (ascending or descending)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of academic levels with optional filtering and sorting.
    """
    levels = [
        {"value": "undergraduate", "label": "Undergraduate"},
        {"value": "masters", "label": "Masters"},
        {"value": "doctoral", "label": "Doctoral/PhD"},
        {"value": "postdoctoral", "label": "Postdoctoral"},
        {"value": "professional", "label": "Professional"}
    ]
    
    return filter_and_sort_options(levels, search, sort_by, sort_order)


@router.get("/target-audiences")
def get_target_audiences(
    search: Optional[str] = Query(None, description="Search term to filter audiences by label or value"),
    sort_by: Optional[SortField] = Query(None, description="Field to sort by"),
    sort_order: Optional[SortOrder] = Query(SortOrder.asc, description="Sort order (ascending or descending)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of target audiences with optional filtering and sorting.
    """
    audiences = [
        {"value": "researchers", "label": "Researchers"},
        {"value": "practitioners", "label": "Practitioners"},
        {"value": "students", "label": "Students"},
        {"value": "educators", "label": "Educators"},
        {"value": "policymakers", "label": "Policymakers"},
        {"value": "general_public", "label": "General Public"},
        {"value": "industry_professionals", "label": "Industry Professionals"},
        {"value": "other", "label": "Other"}
    ]
    
    return filter_and_sort_options(audiences, search, sort_by, sort_order)


@router.get("/research-methodologies")
def get_research_methodologies(
    search: Optional[str] = Query(None, description="Search term to filter methodologies by label or value"),
    sort_by: Optional[SortField] = Query(None, description="Field to sort by"),
    sort_order: Optional[SortOrder] = Query(SortOrder.asc, description="Sort order (ascending or descending)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of research methodologies with optional filtering and sorting.
    """
    methodologies = [
        {"value": "qualitative", "label": "Qualitative"},
        {"value": "quantitative", "label": "Quantitative"},
        {"value": "mixed_methods", "label": "Mixed Methods"},
        {"value": "experimental", "label": "Experimental"},
        {"value": "survey", "label": "Survey Research"},
        {"value": "case_study", "label": "Case Study"},
        {"value": "ethnography", "label": "Ethnography"},
        {"value": "grounded_theory", "label": "Grounded Theory"},
        {"value": "action_research", "label": "Action Research"},
        {"value": "literature_review", "label": "Literature Review"},
        {"value": "meta_analysis", "label": "Meta-Analysis"},
        {"value": "other", "label": "Other"}
    ]
    
    return filter_and_sort_options(methodologies, search, sort_by, sort_order)


@router.get("/countries")
def get_countries(
    search: Optional[str] = Query(None, description="Search term to filter countries by label or value"),
    sort_by: Optional[SortField] = Query(None, description="Field to sort by"),
    sort_order: Optional[SortOrder] = Query(SortOrder.asc, description="Sort order (ascending or descending)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of countries with their academic formatting standards with optional filtering and sorting.
    """
    countries = [
        {"value": "af", "label": "Afghanistan"},
        {"value": "al", "label": "Albania"},
        {"value": "dz", "label": "Algeria"},
        {"value": "ad", "label": "Andorra"},
        {"value": "ao", "label": "Angola"},
        {"value": "ag", "label": "Antigua and Barbuda"},
        {"value": "ar", "label": "Argentina"},
        {"value": "am", "label": "Armenia"},
        {"value": "au", "label": "Australia"},
        {"value": "at", "label": "Austria"},
        {"value": "az", "label": "Azerbaijan"},
        {"value": "bs", "label": "Bahamas"},
        {"value": "bh", "label": "Bahrain"},
        {"value": "bd", "label": "Bangladesh"},
        {"value": "bb", "label": "Barbados"},
        {"value": "by", "label": "Belarus"},
        {"value": "be", "label": "Belgium"},
        {"value": "bz", "label": "Belize"},
        {"value": "bj", "label": "Benin"},
        {"value": "bt", "label": "Bhutan"},
        {"value": "bo", "label": "Bolivia"},
        {"value": "ba", "label": "Bosnia and Herzegovina"},
        {"value": "bw", "label": "Botswana"},
        {"value": "br", "label": "Brazil"},
        {"value": "bn", "label": "Brunei"},
        {"value": "bg", "label": "Bulgaria"},
        {"value": "bf", "label": "Burkina Faso"},
        {"value": "bi", "label": "Burundi"},
        {"value": "cv", "label": "Cabo Verde"},
        {"value": "kh", "label": "Cambodia"},
        {"value": "cm", "label": "Cameroon"},
        {"value": "ca", "label": "Canada"},
        {"value": "cf", "label": "Central African Republic"},
        {"value": "td", "label": "Chad"},
        {"value": "cl", "label": "Chile"},
        {"value": "cn", "label": "China"},
        {"value": "co", "label": "Colombia"},
        {"value": "km", "label": "Comoros"},
        {"value": "cg", "label": "Congo"},
        {"value": "cd", "label": "Congo (Democratic Republic)"},
        {"value": "cr", "label": "Costa Rica"},
        {"value": "ci", "label": "Côte d'Ivoire"},
        {"value": "hr", "label": "Croatia"},
        {"value": "cu", "label": "Cuba"},
        {"value": "cy", "label": "Cyprus"},
        {"value": "cz", "label": "Czech Republic"},
        {"value": "dk", "label": "Denmark"},
        {"value": "dj", "label": "Djibouti"},
        {"value": "dm", "label": "Dominica"},
        {"value": "do", "label": "Dominican Republic"},
        {"value": "ec", "label": "Ecuador"},
        {"value": "eg", "label": "Egypt"},
        {"value": "sv", "label": "El Salvador"},
        {"value": "gq", "label": "Equatorial Guinea"},
        {"value": "er", "label": "Eritrea"},
        {"value": "ee", "label": "Estonia"},
        {"value": "sz", "label": "Eswatini"},
        {"value": "et", "label": "Ethiopia"},
        {"value": "fj", "label": "Fiji"},
        {"value": "fi", "label": "Finland"},
        {"value": "fr", "label": "France"},
        {"value": "ga", "label": "Gabon"},
        {"value": "gm", "label": "Gambia"},
        {"value": "ge", "label": "Georgia"},
        {"value": "de", "label": "Germany"},
        {"value": "gh", "label": "Ghana"},
        {"value": "gr", "label": "Greece"},
        {"value": "gd", "label": "Grenada"},
        {"value": "gt", "label": "Guatemala"},
        {"value": "gn", "label": "Guinea"},
        {"value": "gw", "label": "Guinea-Bissau"},
        {"value": "gy", "label": "Guyana"},
        {"value": "ht", "label": "Haiti"},
        {"value": "hn", "label": "Honduras"},
        {"value": "hu", "label": "Hungary"},
        {"value": "is", "label": "Iceland"},
        {"value": "in", "label": "India"},
        {"value": "id", "label": "Indonesia"},
        {"value": "ir", "label": "Iran"},
        {"value": "iq", "label": "Iraq"},
        {"value": "ie", "label": "Ireland"},
        {"value": "il", "label": "Israel"},
        {"value": "it", "label": "Italy"},
        {"value": "jm", "label": "Jamaica"},
        {"value": "jp", "label": "Japan"},
        {"value": "jo", "label": "Jordan"},
        {"value": "kz", "label": "Kazakhstan"},
        {"value": "ke", "label": "Kenya"},
        {"value": "ki", "label": "Kiribati"},
        {"value": "kp", "label": "Korea (North)"},
        {"value": "kr", "label": "Korea (South)"},
        {"value": "kw", "label": "Kuwait"},
        {"value": "kg", "label": "Kyrgyzstan"},
        {"value": "la", "label": "Laos"},
        {"value": "lv", "label": "Latvia"},
        {"value": "lb", "label": "Lebanon"},
        {"value": "ls", "label": "Lesotho"},
        {"value": "lr", "label": "Liberia"},
        {"value": "ly", "label": "Libya"},
        {"value": "li", "label": "Liechtenstein"},
        {"value": "lt", "label": "Lithuania"},
        {"value": "lu", "label": "Luxembourg"},
        {"value": "mg", "label": "Madagascar"},
        {"value": "mw", "label": "Malawi"},
        {"value": "my", "label": "Malaysia"},
        {"value": "mv", "label": "Maldives"},
        {"value": "ml", "label": "Mali"},
        {"value": "mt", "label": "Malta"},
        {"value": "mh", "label": "Marshall Islands"},
        {"value": "mr", "label": "Mauritania"},
        {"value": "mu", "label": "Mauritius"},
        {"value": "mx", "label": "Mexico"},
        {"value": "fm", "label": "Micronesia"},
        {"value": "md", "label": "Moldova"},
        {"value": "mc", "label": "Monaco"},
        {"value": "mn", "label": "Mongolia"},
        {"value": "me", "label": "Montenegro"},
        {"value": "ma", "label": "Morocco"},
        {"value": "mz", "label": "Mozambique"},
        {"value": "mm", "label": "Myanmar"},
        {"value": "na", "label": "Namibia"},
        {"value": "nr", "label": "Nauru"},
        {"value": "np", "label": "Nepal"},
        {"value": "nl", "label": "Netherlands"},
        {"value": "nz", "label": "New Zealand"},
        {"value": "ni", "label": "Nicaragua"},
        {"value": "ne", "label": "Niger"},
        {"value": "ng", "label": "Nigeria"},
        {"value": "mk", "label": "North Macedonia"},
        {"value": "no", "label": "Norway"},
        {"value": "om", "label": "Oman"},
        {"value": "pk", "label": "Pakistan"},
        {"value": "pw", "label": "Palau"},
        {"value": "ps", "label": "Palestine"},
        {"value": "pa", "label": "Panama"},
        {"value": "pg", "label": "Papua New Guinea"},
        {"value": "py", "label": "Paraguay"},
        {"value": "pe", "label": "Peru"},
        {"value": "ph", "label": "Philippines"},
        {"value": "pl", "label": "Poland"},
        {"value": "pt", "label": "Portugal"},
        {"value": "qa", "label": "Qatar"},
        {"value": "ro", "label": "Romania"},
        {"value": "ru", "label": "Russia"},
        {"value": "rw", "label": "Rwanda"},
        {"value": "kn", "label": "Saint Kitts and Nevis"},
        {"value": "lc", "label": "Saint Lucia"},
        {"value": "vc", "label": "Saint Vincent and the Grenadines"},
        {"value": "ws", "label": "Samoa"},
        {"value": "sm", "label": "San Marino"},
        {"value": "st", "label": "São Tomé and Príncipe"},
        {"value": "sa", "label": "Saudi Arabia"},
        {"value": "sn", "label": "Senegal"},
        {"value": "rs", "label": "Serbia"},
        {"value": "sc", "label": "Seychelles"},
        {"value": "sl", "label": "Sierra Leone"},
        {"value": "sg", "label": "Singapore"},
        {"value": "sk", "label": "Slovakia"},
        {"value": "si", "label": "Slovenia"},
        {"value": "sb", "label": "Solomon Islands"},
        {"value": "so", "label": "Somalia"},
        {"value": "za", "label": "South Africa"},
        {"value": "ss", "label": "South Sudan"},
        {"value": "es", "label": "Spain"},
        {"value": "lk", "label": "Sri Lanka"},
        {"value": "sd", "label": "Sudan"},
        {"value": "sr", "label": "Suriname"},
        {"value": "se", "label": "Sweden"},
        {"value": "ch", "label": "Switzerland"},
        {"value": "sy", "label": "Syria"},
        {"value": "tj", "label": "Tajikistan"},
        {"value": "tz", "label": "Tanzania"},
        {"value": "th", "label": "Thailand"},
        {"value": "tl", "label": "Timor-Leste"},
        {"value": "tg", "label": "Togo"},
        {"value": "to", "label": "Tonga"},
        {"value": "tt", "label": "Trinidad and Tobago"},
        {"value": "tn", "label": "Tunisia"},
        {"value": "tr", "label": "Turkey"},
        {"value": "tm", "label": "Turkmenistan"},
        {"value": "tv", "label": "Tuvalu"},
        {"value": "ug", "label": "Uganda"},
        {"value": "ua", "label": "Ukraine"},
        {"value": "ae", "label": "United Arab Emirates"},
        {"value": "gb", "label": "United Kingdom"},
        {"value": "us", "label": "United States"},
        {"value": "uy", "label": "Uruguay"},
        {"value": "uz", "label": "Uzbekistan"},
        {"value": "vu", "label": "Vanuatu"},
        {"value": "va", "label": "Vatican City"},
        {"value": "ve", "label": "Venezuela"},
        {"value": "vn", "label": "Vietnam"},
        {"value": "ye", "label": "Yemen"},
        {"value": "zm", "label": "Zambia"},
        {"value": "zw", "label": "Zimbabwe"},
        {"value": "other", "label": "Other"}
    ]
    
    return filter_and_sort_options(countries, search, sort_by, sort_order)
