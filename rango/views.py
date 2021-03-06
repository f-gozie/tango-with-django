from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseRedirect
from rango.models import Category
from rango.models import Page, UserProfile
from rango.forms import CategoryForm, UserForm, UserProfileForm, PageForm
from django.contrib.auth.decorators import login_required
from registration.backends.simple.views import RegistrationView
from datetime import datetime
from django.contrib.auth.models import User
# Create your views here.

# More or less a helper method
def get_server_side_cookie(request, cookie, default_val=None):
	val = request.session.get(cookie)
	if not val:
		val = default_val
	return val

def visitor_cookie_handler(request):
	# Get the no of visits to the site with COOKIES.get()
	# If the cookie exists, value returned is casted to an integer, else, default value of 1 is used.
	visits = int(get_server_side_cookie(request, 'visits', '1'))
	last_visit_cookie = get_server_side_cookie(request, 'last_visit', str(datetime.now()))
	last_visit_time = datetime.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')

	# If it's been more than a day since the last visit...
	if (datetime.now() - last_visit_time).seconds > 0:
		visits = visits + 1
		# update the last cookie now that we have updated the count
		request.session['last_visit'] = str(datetime.now())
	else:
		visits = 1
		# set the last visit cookie 
		request.session['last_visit'] = last_visit_cookie
	# Update/set the visits cookie
	request.session['visits'] = visits

def index(request):
	# You first query the database for a list of ALL categories currently stored.
	# Order the categories by no. likes in descending order.
	# Retrieve the top 5 only - or all if less than 5.
	# Place the list in our context dictionary that will be passed to the template engine.
	request.session.set_test_cookie()
	category_list = Category.objects.order_by('-likes')[:5]
	page_list = Page.objects.order_by('-views')[:5]
	context = {'categories': category_list, 'pages':page_list}
	visitor_cookie_handler(request)
	context['visits'] = request.session['visits']
	# context = {'boldmessage': "Crunchy, creamy, cookie, candy, cupcake!"}
	response = render(request, 'rango/index.html', context=context)
	return response

def about(request):
	# if request.session.test_cookie_worked():
	# 	print("TEST COOKIE WORKED...DOPE!!!")
	# 	request.session.delete_test_cookie()
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

@login_required
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

# def register(request):
# 	'''A boolean value for telling the template whether the registration was successful.
# 	Set to false initially. Code changes value to true when registration succeeds.'''
# 	registered = False
# 	if request.method == 'POST':
# 		# Attempt to obtain information from the raw form information. We make use of UserForm and UserProfileForm
# 		user_form = UserForm(data=request.POST)
# 		profile_form = UserProfileForm(data=request.POST)

# 		# If both forms are valid:
# 		if user_form.is_valid() and profile_form.is_valid():
# 			# Save the user's data to the database
# 			user = user_form.save()
# 			# Hash the password with set_password method. Once hashed, update the user object
# 			user.set_password(user.password)
# 			user.save()
# 			# Sort out the UserProfile instance
# 			# We are setting the user attribute ourselves therefore commit=False.
# 			# This delays saving the model until we're ready to avoid integrity problems.
# 			profile = profile_form.save(commit=False)
# 			profile.user = user
# 			# If the user provided a picture, we get it from the input form and put it in the UserProfile model
# 			if 'picture' in request.FILES:
# 				profile.picture = request.FILES['picture']
# 			# We save the UserProfile model instance.
# 			profile.save()
# 			# Update our variable to indicate that the template registration was successful
# 			registered = True
# 		else:
# 			# Invalid form or forms -mistakes or something else?
# 			print(user_form.errors, profile_form.errors)
# 	else:
# 		# Not a HTTP POST, so we render our form using two ModelForm instances.
# 		# Forms will be blank, ready for user input.
# 		user_form = UserForm()
# 		profile_form = UserProfileForm()

# 	# Render the template depending on the context
# 	return render(request, 'rango/register.html', {'user_form':user_form, 'profile_form':profile_form, 'registered':registered})

# def user_login(request):
# 	# If request is a HTTP POST, try pull out the relevant information
# 	# form = UserForm(request.POST or None)
# 	if request.method == 'POST':
# 		'''Gather username and password provided by the user. This info is obtained from the login form
# 		We use request.POST.get('variable') as opposed to request.POST['variable'] because the 
# 		request.POST.get('variable') returns none if the value does not exist, while request.POST['variable']
# 		will raise a KeyError exception.'''
# 		username = request.POST.get('username')
# 		password = request.POST.get('password')

# 		# Use Django's machinery to attempt to see if the username/password combo is valid
# 		# User object is returned if it is
# 		user = authenticate(username=username, password=password)
# 		# If we have a User object, the details are correct
# 		# If None(absence of a value), no user with matching credentials was found.
# 		if user:
# 			# Is the account active or disabled
# 			if user.is_active:
# 				login(request, user)
# 				return HttpResponseRedirect(reverse('index'))
# 			else:
# 				# An inactive account was used, no logging in!
# 				return HttpResponseRedirect("Your account from Agozie's awesome project is disabled!!!!")
# 		else:
# 			form = "Invalid login details"
# 			# Invalid login details
# 			print("Invalid login details:{0}, {1}".format(username, password))
# 			return render(request, 'rango/login.html', {'form':form})
# 	# Request is not a HTTP POST so display the login form. Most likely a HTTP GET.
# 	else:
# 		# No context variables to pass to the template system, hence a blank dictionary object.......
# 		# ask obose the difference between HTTP Get and Http Post
# 		return render(request, 'rango/login.html', {})

def some_view(request):
	if not request.user.is_authenticated():
		return HttpResponse("You are logged in.")
	else:
		return HttpResponse("You are not logged in.")

@login_required
def restricted(request):
	return render(request, 'rango/restricted.html', {})

# @login_required
# def user_logout(request):
# 	logout(request)
# 	return HttpResponseRedirect(reverse('index'))
def track_url(request):
	page_id = None
	if request.method == 'GET':
		if 'page_id' in request.GET:
			page_id = request.GET['page_id']
	if page_id:
		try:
			page = Page.objects.get(id=page_id)
			page.views = page.views + 1
			page.save()
			return redirect(page.url)
		except:
			return HttpResponse("Page id {0} not found".format(page_id))
	print("No page_id in get string")
	return redirect(reverse('index'))

def register_profile(request):
	form = UserProfileForm()
	if request.method == 'POST':
		form = UserProfileForm(request.POST, request.FILES)
		if form.is_valid():
			user_profile = form.save(commit=False)
			user_profile.user = request.user
			user_profile.save()

			return redirect('index')
		else:
			print(form.errors)
	context = {'form':form}

	return render(request, 'rango/profile_registration.html', context)

class MyRegistrationView(RegistrationView):
    def get_success_url(self, user):
        return reverse('register_profile')

@login_required
def profile(request, username):
	try:
		user = User.objects.get(username=username)
	except User.DoesNotExist:
		return redirect('index')

	userprofile = UserProfile.objects.get_or_create(user=user)[0]
	form = UserProfileForm({'website': userprofile.website, 'picture': userprofile.picture})

	if request.method == 'POST':
		form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
		if form.is_valid():
			form.save(commit=True)
			return redirect('profile', user.username)
		else:
			print(form.errors)

	return render(request, 'rango/profile.html', {'userprofile':userprofile, 'selecteduser':user, 'form':form})

@login_required
def list_profiles(request):
	userprofile_list = UserProfile.objects.all()
	return(render(request, 'rango/list_profiles.html', {'userprofile_list' : userprofile_list}))