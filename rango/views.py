from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseRedirect
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm, UserForm, UserProfileForm, PageForm
from django.contrib.auth.decorators import login_required
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

def register(request):
	'''A boolean value for telling the template whether the registration was successful.
	Set to false initially. Code changes value to true when registration succeeds.'''
	registered = False
	if request.method == 'POST':
		# Attempt to obtain information from the raw form information. We make use of UserForm and UserProfileForm
		user_form = UserForm(data=request.POST)
		profile_form = UserProfileForm(data=request.POST)

		# If both forms are valid:
		if user_form.is_valid() and profile_form.is_valid():
			# Save the user's data to the database
			user = user_form.save()
			# Hash the password with set_password method. Once hashed, update the user object
			user.set_password(user.password)
			user.save()
			# Sort out the UserProfile instance
			# We are setting the user attribute ourselves therefore commit=False.
			# This delays saving the model until we're ready to avoid integrity problems.
			profile = profile_form.save(commit=False)
			profile.user = user
			# If the user provided a picture, we get it from the input form and put it in the UserProfile model
			if 'picture' in request.FILES:
				profile.picture = request.FILES['picture']
			# We save the UserProfile model instance.
			profile.save()
			# Update our variable to indicate that the template registration was successful
			registered = True
		else:
			# Invalid form or forms -mistakes or something else?
			print(user_form.errors, profile_form.errors)
	else:
		# Not a HTTP POST, so we render our form using two ModelForm instances.
		# Forms will be blank, ready for user input.
		user_form = UserForm()
		profile_form = UserProfileForm()

	# Render the template depending on the context
	return render(request, 'rango/register.html', {'user_form':user_form, 'profile_form':profile_form, 'registered':registered})

def user_login(request):
	# If request is a HTTP POST, try pull out the relevant information
	if request.method == 'POST':
		'''Gather username and password provided by the user. This info is obtained from the login form
		We use request.POST.get('variable') as opposed to request.POST['variable'] because the 
		request.POST.get('variable') returns none if the value does not exist, while request.POST['variable']
		will raise a KeyError exception.'''
		username = request.POST.get('username')
		password = request.POST.get('password')

		# Use Django's machinery to attempt to see if the username/password combo is valid
		# User object is returned if it is
		user = authenticate(username=username, password=password)
		# If we have a User object, the details are correct
		# If None(absence of a value), no user with matching credentials was found.
		if user:
			# Is the account active or disabled
			if user.is_active:
				login(request, user)
				return HttpResponseRedirect(reverse('index'))
			else:
				# An inactive account was used, no logging in!
				return HttpResponseRedirect("Your account from Agozie's awesome project is disabled!!!!")
		else:
			# Invalid login details
			print("Invalid login details:{0}, {1}".format(username, password))
			return HttpResponse("Sorry FAM, either your credentials are wrong or you're a SCAM! HAHAHA!!!")
	# Request is not a HTTP POST so display the login form. Most likely a HTTP GET.
	else:
		# No context variables to pass to the template system, hence a blank dictionary object.......
		# ask obose the difference between HTTP Get and Http Post
		return render(request, 'rango/login.html', {})

def some_view(request):
	if not request.user.is_authenticated():
		return HttpResponse("You are logged in.")
	else:
		return HttpResponse("You are not logged in.")

@login_required
def restricted(request):
	return HttpResponse("Since you're logged in, you can see this text!")

@login_required
def user_logout(request):
	logout(request)
	return HttpResponseRedirect(reverse('index'))