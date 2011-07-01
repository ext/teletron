##
# Requires LCDproc
#
#
require 'socket'

server="localhost"
local_port=4851
remote_port=13666
title="The Grid"

class LCD

	def initialize(server,port,title)
		puts "Connecting..."
		@socket = TCPSocket.open(server,port)
		if @socket
			puts "Connected"
			read_server
			
			write("hello");
			create_title(title)
			@rows=Array.new 3 {|i| Row.new self,(i+2) }
		else
			puts "ERROR!"
		end
	end

	def create_title(title)
		write("screen_add 1");
		write("screen_set 1 priority 1");
		write("widget_add 1 1 title");
		write("widget_set 1 1 \"#{title}\"");
	end

	def read_server
		@thread = Thread.start do
			puts "New thread"
			loop do
				data = @socket.recv(1024)
				puts data
			end
		end
	end

	def join
		@thread.join
	end

	def write(data)
		puts "> #{data}"
		@socket.puts(data)
	end

	def push_content(data)
		@rows[2].content=@rows[1].content
		@rows[1].content=@rows[0].content
		@rows[0].content=data
		@rows.each {|r| r.update }
	end

end

class Row
	
	attr_accessor :content

	def initialize(lcd,row)
		@lcd=lcd
		@row = row
		lcd.write "widget_add 1 #{row} scroller"
		@content=""
	end

	def update
		@lcd.write "widget_set 1 #@row 1 #@row 20 #@row h 2 \"#@content\""
	end
end


lcd=LCD.new server,remote_port,title

sck=UDPSocket.new
sck.bind(nil,local_port)
loop do
	text, sender = sck.recvfrom(1024)
	text.chomp!
	lcd.push_content text
	puts "$ Pushed #{text} to display"
end

lcd.join

