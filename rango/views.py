from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from rango.forms import PageForm
# Create your views here.
def index(request):
	# You first query the database for a list of ALL categories currently stored.
	# Order the categories by no. likes in descending order.
	# Retrieve the top 5 only - or all if less than 5.
	# Place the list in our context dictionary that will be passed to the template engine.
	category_list = Category.objects.order_by('-likes')[:5]
	view_list = Page.objects.order_by('-views')[:5]
	context = {'categories': category_list, 'views':view_list}
	# context = {'boldmessage': "Crunchy, creamy, cookie, candy, cupcake!"}
	return render(request, 'rango/index.html', context=context)

def about(request):
	return render(request, 'rango/about.html', {})

def show_category(request, category_name_slug):
	# creating a context dictionary that can be passed to the template rendering engine
	context = {}

	try:
		# Check if we can find a category name slug with the given name
		# If we cant, the .get() raises a DoesNotExist exception
		# If we can, the .get() returns one model instance
		category = Category.objects.get(slug=category_name_slug)

		# We then retrieve all the associated pages
		# Note that filter() returns a list of page objects or an empty list
		pages = Page.objects.filter(category=category)

		# Add our results list to the template context under the name pages
		context['pages']=pages
		# Add the category object from the database to the context dictionary
		# We'll use this in the template to verify that the category exists.
		context['category']=category
	except Category.DoesNotExist:
		# This is if we didnt find the specified category
		context['category'] = None
		context['pages'] = None

	# Render the response and return it to the client
	return render(request, 'rango/category.html', context)

def add_category(request):
	form = CategoryForm()
	# Ask yourself, is it a HTTP POST
	if request.method == "POST":
		form = CategoryForm(request.POST)
		# Is the form valid?
		if form.is_valid():
			# Save the new category into the database
			form.save(commit=True)
			'''Now that the category is saved, we could give a confirmation message
			But since the most recent category added is on the index page, we can then direct the user to the index page'''
			return index(request)
		else:
			# If the supplied form contained errors, just print them to the terminal
			print(form.errors)
		# Will handle the bad form, new form, or no form supplied cases
		# Render the form with error messages (if any)
	return render(request, 'rango/add_category.html', {'form':form})

def add_page(request, category_name_slug):
	try: 
		category = Category.objects.get(slug=category_name_slug)
	except Category.DoesNotExist:
		category = None

	form = PageForm()
	if request.method == 'POST':
		form = PageForm(request.POST)
		if form.is_valid():
			if category:
				page = form.save(commit=False)
				page.category = category
				page.views = 0
				page.save()
				return show_category(request, category_name_slug)
		else:
			print(form.errors)

	context = {'form':form, 'category':category}
	return render(request, 'rango/add_page.html', context)